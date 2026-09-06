"""
LLM-dependent RAG comparison experiment.

Companion to app/retrieval_eval.py (which covers retrieval-only metrics with
no LLM calls). This script exercises the REAL agent loop (app.agent.run_agent)
under each of the three retrieval conditions and measures:

  * unsupported_number_rate -- fraction of numeric tokens in the agent's
                                final answer that do NOT appear in any tool
                                output for that turn (a proxy for
                                hallucinated/invented figures).
  * faithfulness            -- whether the agent's answer states the SAME
                                risk category / recommended category as the
                                authoritative profile, when asked a question
                                that should surface them.
  * latency_ms / total_tokens -- from app.agent.run_agent's instrumentation.

Requires a real GROQ_API_KEY in backend/.env (or the environment) and
network access to the Groq API. Run with:

    cd backend
    python -m scripts.run_rag_experiment

Results are written to scripts/rag_experiment_results.json.

NOTE: this script was authored and is ready to run, but was NOT executed as
part of building this repository, because the sandbox used to build it has
no network access to the Groq API. Numbers it prints/saves are only
meaningful once you run it yourself with a valid key.
"""

import json
import re
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agent import run_agent
from app.retrieval import build_profile_context, rank_conversations, MODES


@dataclass
class FakeProfile:
    income: float = 90000
    expenses: float = 50000
    savings: float = 40000
    planned_investment: float = 15000
    goal: str = "Long-term wealth creation"
    horizon_years: int = 12


@dataclass
class FakeRisk:
    score: int = 30
    risk_category: str = "Moderate"
    responses: list = field(default_factory=lambda: [3, 4, 3, 4, 3, 4, 3, 4])


@dataclass
class FakeRecommendation:
    category: str = "Balanced Advantage / Index Funds"
    rationale: str = "Balances growth and stability, suited to a longer runway."


@dataclass
class FakeConversation:
    id: int
    query: str
    response: str
    created_at: datetime


def make_history(n: int = 30) -> list[FakeConversation]:
    now = datetime.utcnow()
    templates = [
        ("What's my savings rate?", "Your savings rate is currently healthy given your income and expenses."),
        ("Am I on track for retirement?", "Your long-term wealth creation goal appears on track given your horizon."),
        ("What funds match my profile?", "Balanced Advantage and Index funds match your Moderate risk category."),
    ]
    return [
        FakeConversation(
            id=i, query=templates[i % 3][0], response=templates[i % 3][1],
            created_at=now - timedelta(days=(i * 7) % 500),
        )
        for i in range(n)
    ]


TEST_QUESTIONS = [
    "How suitable is my current investment approach given my risk profile?",
    "What real funds match my recommended category?",
    "How much can I safely invest each month?",
    "Is my financial goal realistic given my income and expenses?",
]

NUMBER_RE = re.compile(r"-?\d[\d,]*\.?\d*")


def extract_numbers(text: str) -> set[str]:
    return {n.replace(",", "") for n in NUMBER_RE.findall(text)}


def tool_output_numbers(tool_trace: list[dict]) -> set[str]:
    numbers = set()
    for call in tool_trace:
        blob = json.dumps(call.get("output", {}))
        numbers |= extract_numbers(blob)
    return numbers


def build_context_for_mode(mode: str, query: str, history: list[FakeConversation]) -> tuple[dict, list[dict]]:
    profile, risk, rec = FakeProfile(), FakeRisk(), FakeRecommendation()
    facts, sources = build_profile_context(profile, risk, rec)

    if mode == "no_memory":
        return {"authoritative_profile": facts, "retrieved_memories": []}, sources
    if mode == "full_history":
        memories = [{"id": c.id, "query": c.query, "response": c.response,
                     "created_at": c.created_at.isoformat()} for c in history]
        return {"authoritative_profile": facts, "retrieved_memories": memories}, sources
    if mode == "lexical_rag":
        top = rank_conversations(history, query, limit=4)
        memories = [{"id": c.id, "query": c.query, "response": c.response,
                     "created_at": c.created_at.isoformat()} for c in top]
        return {"authoritative_profile": facts, "retrieved_memories": memories}, sources
    raise ValueError(mode)


def run_experiment(n_history: int = 30) -> dict:
    history = make_history(n_history)
    results = {mode: {"unsupported_rates": [], "faithful": [], "latency_ms": [], "total_tokens": []} for mode in MODES}

    for mode in MODES:
        for question in TEST_QUESTIONS:
            context, sources = build_context_for_mode(mode, question, history)
            result = run_agent(question, context, retrieval_sources=sources)

            answer = result["answer"]
            answer_numbers = extract_numbers(answer)
            grounded_numbers = tool_output_numbers(result["tool_trace"])
            # ignore tiny numbers (years, list positions) which are commonly
            # fine to state without a tool call (e.g. "12 years")
            checkable = {n for n in answer_numbers if len(n.replace("-", "").replace(".", "")) > 2}
            unsupported = checkable - grounded_numbers
            rate = len(unsupported) / len(checkable) if checkable else 0.0

            faithful = ("Moderate" in answer) or ("Balanced Advantage" in answer) or ("Index Funds" in answer)

            results[mode]["unsupported_rates"].append(rate)
            results[mode]["faithful"].append(faithful)
            results[mode]["latency_ms"].append(result.get("latency_ms", 0.0))
            results[mode]["total_tokens"].append(result.get("total_tokens", 0))

    summary = {}
    for mode, r in results.items():
        summary[mode] = {
            "mean_unsupported_number_rate": round(statistics.mean(r["unsupported_rates"]), 4),
            "faithfulness_rate": round(sum(r["faithful"]) / len(r["faithful"]), 4),
            "mean_latency_ms": round(statistics.mean(r["latency_ms"]), 2),
            "mean_total_tokens": round(statistics.mean(r["total_tokens"]), 1),
            "n_questions": len(TEST_QUESTIONS),
        }
    return summary


if __name__ == "__main__":
    summary = run_experiment()
    out_path = Path(__file__).resolve().parent / "rag_experiment_results.json"
    out_path.write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    print(f"\nSaved to {out_path}")
