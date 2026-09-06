"""
Integration test for the Groq AI Advisor agent.

Tests:
1. Groq API connectivity with the provided API key
2. Tool-calling loop (agent correctly delegates to deterministic tools)
3. Full end-to-end API test using the FastAPI test client (signup → profile → risk → agent query)
4. Currency guardrail (response must use ₹, not $)

Run with:
    cd investright_app/backend
    python -m pytest tests/test_groq_agent.py -v
"""
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.agent import run_agent, normalize_indian_currency


def unique_email(prefix="test"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"


# ---------------------------------------------------------------------------
# 1. Unit: currency normalizer
# ---------------------------------------------------------------------------

def test_normalize_indian_currency_replaces_dollar():
    result = normalize_indian_currency("You have $5,000 in USD savings.")
    assert "$" not in result
    assert "₹" in result
    assert "USD" not in result


def test_normalize_indian_currency_leaves_rupee_symbol():
    result = normalize_indian_currency("Your balance is ₹1,00,000.")
    assert "₹1,00,000" in result


# ---------------------------------------------------------------------------
# 2. Unit: tools are callable without LLM
# ---------------------------------------------------------------------------

def test_financial_analysis_tool():
    from app.agent import tool_financial_analysis
    result = tool_financial_analysis(income=80000, expenses=50000, planned_investment=10000)
    assert result["monthly_savings"] == 30000
    assert result["investment_capacity"] == 20000
    assert "savings_rate_pct" in result


def test_risk_assessment_tool():
    from app.agent import tool_risk_assessment
    result = tool_risk_assessment(responses=[1, 1, 1, 1, 1, 1, 1, 1])
    assert result["risk_category"] == "Conservative"
    result2 = tool_risk_assessment(responses=[5, 5, 5, 5, 5, 5, 5, 5])
    assert result2["risk_category"] == "Aggressive"


def test_goal_analysis_tool():
    from app.agent import tool_goal_analysis
    result = tool_goal_analysis(goal="Buy a house", horizon_years=10)
    assert result["horizon_bucket"] == "long"
    result2 = tool_goal_analysis(goal="Emergency fund", horizon_years=2)
    assert result2["horizon_bucket"] == "short"


def test_investment_matching_tool():
    from app.agent import tool_investment_matching
    result = tool_investment_matching(risk_category="Conservative", horizon_bucket_value="short")
    assert "Liquid" in result["recommended_category"] or "Fixed" in result["recommended_category"]
    result2 = tool_investment_matching(risk_category="Aggressive", horizon_bucket_value="long")
    assert "Equity" in result2["recommended_category"] or "Multi" in result2["recommended_category"]


def test_platform_lookup_tool():
    from app.agent import tool_platform_lookup
    result = tool_platform_lookup(category_focus="equity")
    assert "platforms" in result
    assert isinstance(result["platforms"], list)


# ---------------------------------------------------------------------------
# 3. Live Groq API integration (requires real API key in .env)
# ---------------------------------------------------------------------------

def test_groq_api_connectivity_and_basic_response():
    """Tests that the Groq API key is valid and the model responds."""
    from app.config import settings
    if not settings.groq_api_key:
        pytest.skip("GROQ_API_KEY not set — skipping live API test")

    user_context = {
        "authoritative_profile": {
            "currency": "INR",
            "income_inr_per_month": 100000,
            "expenses_inr_per_month": 60000,
            "savings_inr": 500000,
            "planned_investment_inr_per_month": 15000,
            "goal": "Retirement",
            "horizon_years": 20,
            "risk_score": 30,
            "risk_category": "Moderate",
        },
        "retrieved_memories": [],
    }

    result = run_agent("What is my monthly savings?", user_context)

    assert "answer" in result
    assert len(result["answer"]) > 10
    assert "tool_trace" in result
    assert result["latency_ms"] > 0


def test_groq_agent_uses_tools_not_hallucination():
    """The agent must call at least one tool when given raw numbers to process."""
    from app.config import settings
    if not settings.groq_api_key:
        pytest.skip("GROQ_API_KEY not set — skipping live API test")

    user_context = {
        "authoritative_profile": {
            "currency": "INR",
            "income_inr_per_month": 120000,
            "expenses_inr_per_month": 80000,
            "savings_inr": 200000,
            "planned_investment_inr_per_month": 20000,
            "goal": "Child education",
            "horizon_years": 12,
            # No risk_category provided — agent must call tools to compute it
        },
        "retrieved_memories": [],
    }

    result = run_agent(
        "Calculate my savings rate and tell me the exact monthly savings amount.",
        user_context,
    )

    # Answer must be present and non-empty
    assert "answer" in result
    assert len(result["answer"]) > 10, f"Unexpectedly short answer: {result['answer']}"
    # Answer should be in rupees
    answer = result["answer"]
    assert "$" not in answer, f"Answer contains dollar sign: {answer}"
    # Tool trace should have at least the financial_analysis call
    tool_names = [t["tool"] for t in result["tool_trace"]]
    assert "financial_analysis" in tool_names, (
        f"Expected financial_analysis tool call, got: {tool_names}\nAnswer: {answer}"
    )


def test_groq_agent_currency_guardrail():
    """Verify the normalize_indian_currency post-processing catches any USD leakage."""
    from app.config import settings
    if not settings.groq_api_key:
        pytest.skip("GROQ_API_KEY not set — skipping live API test")

    user_context = {
        "authoritative_profile": {
            "currency": "INR",
            "income_inr_per_month": 50000,
            "expenses_inr_per_month": 30000,
            "savings_inr": 100000,
            "planned_investment_inr_per_month": 5000,
            "goal": "House purchase",
            "horizon_years": 7,
        },
        "retrieved_memories": [],
    }

    result = run_agent("Give me a brief investment summary.", user_context)
    assert "$" not in result["answer"]


# ---------------------------------------------------------------------------
# 4. End-to-end API test via FastAPI TestClient
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth_token(client):
    """Register a test user and return bearer token."""
    email = unique_email("fixture")
    resp = client.post("/api/auth/signup", json={
        "email": email,
        "full_name": "Test User",
        "password": "testpassword123",
        "age": 30,
    })
    assert resp.status_code == 200, f"Signup failed: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture(scope="module")
def authed_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


def test_health_check(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_signup_and_login(client):
    email = unique_email("login")
    signup = client.post("/api/auth/signup", json={
        "email": email,
        "full_name": "Login Test",
        "password": "password123",
    })
    assert signup.status_code == 200, f"Signup failed: {signup.text}"

    login = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    assert login.status_code == 200
    assert "access_token" in login.json()


def test_get_me(client, authed_headers):
    resp = client.get("/api/auth/me", headers=authed_headers)
    assert resp.status_code == 200
    assert resp.json()["email"].endswith("@example.com")


def test_save_and_get_profile(client, authed_headers):
    profile_data = {
        "income": 100000,
        "expenses": 60000,
        "savings": 300000,
        "planned_investment": 15000,
        "goal": "Retirement",
        "horizon_years": 20,
    }
    save = client.post("/api/profile", json=profile_data, headers=authed_headers)
    assert save.status_code == 200, f"Profile save failed: {save.text}"

    get = client.get("/api/profile", headers=authed_headers)
    assert get.status_code == 200
    assert get.json()["income"] == 100000


def test_risk_assessment_api(client, authed_headers):
    # Ensure profile exists
    client.post("/api/profile", json={
        "income": 100000, "expenses": 60000, "savings": 300000,
        "planned_investment": 15000, "goal": "Retirement", "horizon_years": 20,
    }, headers=authed_headers)

    resp = client.post("/api/risk-assessment", json={"responses": [3, 3, 3, 3, 3, 3, 3, 3]},
                       headers=authed_headers)
    assert resp.status_code == 200, f"Risk assessment failed: {resp.text}"
    data = resp.json()
    assert data["risk_category"] in ("Conservative", "Moderate", "Aggressive")
    assert data["score"] == 24


def test_dashboard_api(client, authed_headers):
    resp = client.get("/api/dashboard", headers=authed_headers)
    assert resp.status_code == 200, f"Dashboard failed: {resp.text}"
    data = resp.json()
    assert "monthly_savings" in data
    assert data["monthly_savings"] == 40000.0
    assert data["recommended_category"] is not None


def test_agent_api_live(client, authed_headers):
    """Full end-to-end: query the AI advisor via the HTTP API."""
    from app.config import settings
    if not settings.groq_api_key:
        pytest.skip("GROQ_API_KEY not set — skipping live agent API test")

    resp = client.post(
        "/api/agent/query",
        json={"message": "What is my monthly investment capacity?"},
        headers=authed_headers,
    )
    assert resp.status_code == 200, f"Agent query failed: {resp.text}"
    data = resp.json()
    assert "answer" in data
    assert len(data["answer"]) > 5
    assert "tool_trace" in data


def test_portfolio_add_and_list(client, authed_headers):
    add = client.post("/api/portfolio", json={
        "name": "Axis Bluechip Fund",
        "asset_type": "equity",
        "invested_amount": 50000,
        "current_value": 58000,
    }, headers=authed_headers)
    assert add.status_code == 201, f"Portfolio add failed: {add.text}"

    get = client.get("/api/portfolio", headers=authed_headers)
    assert get.status_code == 200
    portfolio = get.json()
    assert portfolio["total_invested"] >= 50000
    holding_ids = [h["id"] for h in portfolio["holdings"]]
    assert len(holding_ids) > 0

    # cleanup
    del_resp = client.delete(f"/api/portfolio/{holding_ids[-1]}", headers=authed_headers)
    assert del_resp.status_code == 204


def test_conversations_are_persisted(client, authed_headers):
    """After an agent query, conversation history should be accessible."""
    from app.config import settings
    if not settings.groq_api_key:
        pytest.skip("GROQ_API_KEY not set — skipping live agent API test")

    client.post(
        "/api/agent/query",
        json={"message": "Give me a one-sentence investment tip."},
        headers=authed_headers,
    )

    convos = client.get("/api/agent/conversations", headers=authed_headers)
    assert convos.status_code == 200
    assert len(convos.json()) >= 1
