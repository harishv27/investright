"""
AI Advisor Agent -- real tool-calling implementation (paper Section 4).

The LLM never computes numbers itself. It only decides which deterministic
tool to call and when, then explains the results in natural language.
"""

import json
import time

from groq import Groq
import requests

from app.config import settings
from app.analytics import calculate_financials
from app.risk import score_risk
from app.recommendation import match_investment_category, horizon_bucket

client = Groq(api_key=settings.groq_api_key) if settings.groq_api_key else None


# ---------------------------------------------------------------------------
# Curated (non-live) platform data. No free API publishes this -- maintain
# it yourself and keep it current.
# ---------------------------------------------------------------------------

PLATFORM_DB = [
    {"name": "Example Platform A", "min_investment": 500, "supports": ["equity", "debt", "hybrid"],
     "fee_note": "Direct plans, no commission. Verify current fees on the provider's site."},
    {"name": "Example Platform B", "min_investment": 100, "supports": ["equity", "hybrid"],
     "fee_note": "Regular plans, distributor commission applies. Verify current fees on the provider's site."},
]


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def tool_financial_analysis(income: float, expenses: float, planned_investment: float):
    return calculate_financials(income, expenses, planned_investment)


def tool_risk_assessment(responses: list[int]):
    return score_risk(responses)


def tool_goal_analysis(goal: str, horizon_years: int):
    return {"goal": goal, "horizon_years": horizon_years, "horizon_bucket": horizon_bucket(horizon_years)}


def tool_investment_matching(risk_category: str, horizon_bucket_value: str):
    # horizon_bucket_value is already "short"/"long"; reuse the table directly
    from app.recommendation import INVESTMENT_MATCH_TABLE
    category, rationale = INVESTMENT_MATCH_TABLE[(risk_category, horizon_bucket_value)]
    return {"recommended_category": category, "rationale": rationale}


def tool_fund_lookup(scheme_category_keyword: str, limit: int = 5):
    try:
        resp = requests.get(
            "https://api.mfapi.in/mf/search",
            params={"q": scheme_category_keyword},
            timeout=5,
        )
        resp.raise_for_status()
        results = resp.json()[:limit]
        return {"matches": results, "source": "mfapi.in", "count": len(results)}
    except requests.RequestException as e:
        return {"error": f"Could not reach fund data source: {e}"}


def tool_platform_lookup(category_focus: str = None):
    matches = [p for p in PLATFORM_DB if category_focus is None or category_focus in p["supports"]]
    return {"platforms": matches, "note": "Curated data -- verify current fees on the provider's own site."}


TOOL_IMPLEMENTATIONS = {
    "financial_analysis": tool_financial_analysis,
    "risk_assessment": tool_risk_assessment,
    "goal_analysis": tool_goal_analysis,
    "investment_matching": tool_investment_matching,
    "fund_lookup": tool_fund_lookup,
    "platform_lookup": tool_platform_lookup,
}


# ---------------------------------------------------------------------------
# Tool schemas sent to the API
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "financial_analysis",
        "description": "Calculates monthly savings, savings rate, expense ratio, and "
                        "remaining investment capacity from income and expenses.",
        "input_schema": {
            "type": "object",
            "properties": {
                "income": {"type": "number"},
                "expenses": {"type": "number"},
                "planned_investment": {"type": "number"},
            },
            "required": ["income", "expenses", "planned_investment"],
        },
    },
    {
        "name": "risk_assessment",
        "description": "Scores risk questionnaire responses (each 1-5) and returns "
                        "the risk category: Conservative, Moderate, or Aggressive.",
        "input_schema": {
            "type": "object",
            "properties": {
                "responses": {"type": "array", "items": {"type": "integer"}},
            },
            "required": ["responses"],
        },
    },
    {
        "name": "goal_analysis",
        "description": "Classifies the user's financial goal and horizon into a "
                        "short (<5yr) or long (>=5yr) horizon bucket.",
        "input_schema": {
            "type": "object",
            "properties": {
                "goal": {"type": "string"},
                "horizon_years": {"type": "integer"},
            },
            "required": ["goal", "horizon_years"],
        },
    },
    {
        "name": "investment_matching",
        "description": "Looks up the recommended investment category given a risk "
                        "category and horizon bucket. Call AFTER risk_assessment and "
                        "goal_analysis.",
        "input_schema": {
            "type": "object",
            "properties": {
                "risk_category": {"type": "string", "enum": ["Conservative", "Moderate", "Aggressive"]},
                "horizon_bucket_value": {"type": "string", "enum": ["short", "long"]},
            },
            "required": ["risk_category", "horizon_bucket_value"],
        },
    },
    {
        "name": "fund_lookup",
        "description": "Searches real, currently-listed mutual fund schemes matching a "
                        "category keyword via a live free data source. Use AFTER "
                        "investment_matching. Never invent a fund name yourself.",
        "input_schema": {
            "type": "object",
            "properties": {
                "scheme_category_keyword": {"type": "string"},
                "limit": {"type": "integer", "default": 5},
            },
            "required": ["scheme_category_keyword"],
        },
    },
    {
        "name": "platform_lookup",
        "description": "Returns a curated, non-live list of investment platforms "
                        "supporting a category focus. Informational only -- never "
                        "describe a result as 'the best'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category_focus": {"type": "string", "enum": ["equity", "debt", "hybrid"]},
            },
        },
    },
]


SYSTEM_PROMPT = """You are Fin, a financial decision-support assistant.

This app is for users in India. All money values are Indian rupees (INR).
Always write the rupee symbol ₹ and Indian digit grouping, such as ₹1,00,000.
Never use $, USD, dollars, or other foreign currency symbols. Do not convert
the values to another currency.

Rules you must always follow:
- You have ONLY 6 tools available: financial_analysis, risk_assessment, goal_analysis, investment_matching, fund_lookup, platform_lookup.
- NEVER call or invent any other tool name (e.g. do NOT call 'commentary', 'calculator', etc.).
- Never calculate, estimate, or invent any financial number yourself. Every
  number in your answer must come from a tool result.
- For evaluating income, expenses, and investment capacity, use financial_analysis.
- Use the available tools to gather what you need before answering.
- Call risk_assessment and goal_analysis before investment_matching, since
  investment_matching needs their outputs as input.
- If you're missing information needed for a tool, ask the user instead of
  guessing.
- Always make clear this is decision support, not licensed financial advice,
  and that recommendations are not guarantees of investment performance.
- When mentioning specific funds or platforms, present them as examples that
  fit the matched category, never as "the best" or a personal endorsement.
  Note that details can change and should be verified on the provider's site.
- Keep answers concise and grounded in the specific tool outputs you received.
"""


def normalize_indian_currency(text: str) -> str:
    return (text.replace("$", "₹").replace("USD", "INR").replace("usd", "inr")
            .replace("dollars", "rupees").replace("Dollars", "Rupees"))


def run_agent(
    user_message: str,
    user_context: dict,
    conversation_history: list = None,
    retrieval_sources: list[dict] = None,
) -> dict:
    if client is None:
        return {
            "answer": "The AI advisor isn't configured yet. Add a GROQ_API_KEY "
                      "to the backend's .env file to enable this feature.",
            "tool_trace": [],
            "retrieval_sources": retrieval_sources or [],
            "latency_ms": 0.0,
            "total_tokens": 0,
        }

    messages = conversation_history[:] if conversation_history else []
    messages.append({
        "role": "user",
        "content": f"Authoritative user context: {json.dumps(user_context)}\n\n"
                   f"Use retrieved memories only as supporting context; current structured facts "
                   f"override memories. Retrieved context: {json.dumps(user_context.get('retrieved_memories', []))}\n\n"
                   f"User's question: {user_message}",
    })

    tool_trace = []
    total_tokens = 0
    start_time = time.perf_counter()

    while True:
        try:
            response = client.chat.completions.create(
                model=settings.groq_model,
                max_tokens=1024,
                temperature=0.2,
                messages=[{"role": "system", "content": SYSTEM_PROMPT}, *messages],
                tools=[{"type": "function", "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"],
                }} for tool in TOOLS],
            )
        except Exception as err:
            if "tool" in str(err).lower():
                response = client.chat.completions.create(
                    model=settings.groq_model,
                    max_tokens=1024,
                    temperature=0.2,
                    messages=[{"role": "system", "content": SYSTEM_PROMPT}, *messages],
                )
            else:
                raise
        usage = getattr(response, "usage", None)
        if usage is not None:
            total_tokens += getattr(usage, "total_tokens", 0) or 0

        message = response.choices[0].message
        tool_calls = message.tool_calls or []

        if not tool_calls:
            return {
                "answer": normalize_indian_currency(message.content or ""),
                "tool_trace": tool_trace,
                "retrieval_sources": retrieval_sources or [],
                "latency_ms": round((time.perf_counter() - start_time) * 1000, 2),
                "total_tokens": total_tokens,
            }

        messages.append(message.model_dump(exclude_none=True))

        tool_results = []
        for tool_call in tool_calls:
            function = tool_call.function
            fn = TOOL_IMPLEMENTATIONS.get(function.name)
            try:
                tool_input = json.loads(function.arguments)
                result = fn(**tool_input) if fn else {"error": f"Unknown tool {function.name}"}
                tool_trace.append({"tool": function.name, "input": tool_input, "output": result})
            except Exception as e:
                result = {"error": str(e)}
                tool_trace.append({"tool": function.name, "input": function.arguments, "error": str(e)})

            tool_results.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result),
            })

        messages.extend(tool_results)
