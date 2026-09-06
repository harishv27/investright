"""
Retrieval layer for the AI advisor (paper Section III-E).

Supports three retrieval conditions, selectable via `mode`, so they can be
compared directly (see app/retrieval_eval.py and scripts/run_rag_experiment.py):

- "no_memory"    -- authoritative structured facts only, no conversation
                    history at all.
- "full_history" -- authoritative facts + every prior conversation for the
                    user, unranked, most recent first.
- "lexical_rag"  -- authoritative facts + a small, lexically-ranked,
                    recency-weighted subset of prior conversations
                    (the production default).

In every mode, authoritative facts are attached first and explicitly tagged
as authoritative; conversational memory (if any) is attached second and
tagged as non-authoritative, so the caller (the agent's system prompt) can
be instructed to let current facts override older conversational claims.

The ranking core (`rank_conversations`) is a pure function over plain
dicts/objects with `.query`, `.response`, `.created_at` -- it does not touch
the database, so it can be unit-tested and benchmarked directly (see
app/retrieval_eval.py) without a running Postgres instance.
"""

import re
from datetime import datetime

MODES = ("no_memory", "full_history", "lexical_rag")


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))


def build_profile_context(profile, latest_risk, recommendation) -> tuple[dict, list[dict]]:
    if not profile:
        return {"status": "incomplete", "message": "No completed financial profile is available yet."}, []

    facts = {
        "currency": "INR",
        "income_inr_per_month": profile.income,
        "expenses_inr_per_month": profile.expenses,
        "savings_inr": profile.savings,
        "planned_investment_inr_per_month": profile.planned_investment,
        "goal": profile.goal,
        "horizon_years": profile.horizon_years,
    }
    sources = [{"type": "financial_profile", "label": "Current financial profile"}]
    if latest_risk:
        facts["risk_score"] = latest_risk.score
        facts["risk_category"] = latest_risk.risk_category
        facts["risk_responses"] = latest_risk.responses
        sources.append({"type": "risk_assessment", "label": "Latest risk assessment"})
    if recommendation:
        facts["recommended_category"] = recommendation.category
        facts["recommendation_rationale"] = recommendation.rationale
        sources.append({"type": "recommendation", "label": "Latest recommendation"})
    return facts, sources


def rank_conversations(conversations: list, query: str, limit: int = 4, now: datetime = None) -> list:
    """Pure lexical-overlap + recency ranking over a list of conversation-like
    objects (must expose .query, .response, .created_at). No DB access.
    """
    now = now or datetime.utcnow()
    query_tokens = _tokens(query)
    ranked = []
    for conversation in conversations:
        text = f"{conversation.query} {conversation.response}"
        overlap = len(query_tokens & _tokens(text))
        age_days = max(0, (now - conversation.created_at).days)
        age_bonus = max(0, 1 - age_days / 365)
        ranked.append((overlap + age_bonus, conversation))
    ranked.sort(key=lambda item: (item[0], item[1].created_at), reverse=True)
    return [c for _, c in ranked[:limit]]


def _memory_entries(conversations: list, source_label: str) -> tuple[list[dict], list[dict]]:
    memories, sources = [], []
    for conversation in conversations:
        memories.append({
            "id": conversation.id,
            "query": conversation.query,
            "response": conversation.response[:1200],
            "created_at": conversation.created_at.isoformat(),
        })
        sources.append({"type": "conversation", "id": conversation.id, "label": source_label})
    return memories, sources


def retrieve_user_context(
    db,
    user_id: int,
    query: str,
    profile,
    latest_risk,
    recommendation,
    limit: int = 4,
    mode: str = "lexical_rag",
    history_query_limit: int = 500,
) -> tuple[dict, list[dict]]:
    """Assemble agent context under the given retrieval `mode`.

    `db` may be None when mode == "no_memory" (no query needed).
    """
    if mode not in MODES:
        raise ValueError(f"Unknown retrieval mode: {mode!r}. Expected one of {MODES}.")

    from app import models  # local import: keeps this module DB-import-optional

    profile_facts, sources = build_profile_context(profile, latest_risk, recommendation)

    if mode == "no_memory":
        return {"authoritative_profile": profile_facts, "retrieved_memories": []}, sources

    conversations_query = (
        db.query(models.Conversation)
        .filter(models.Conversation.user_id == user_id)
        .order_by(models.Conversation.created_at.desc())
    )

    if mode == "full_history":
        conversations = conversations_query.all()
        memories, mem_sources = _memory_entries(conversations, "Prior advisor conversation (full history)")
        sources.extend(mem_sources)
        return {"authoritative_profile": profile_facts, "retrieved_memories": memories}, sources

    # lexical_rag (default / production mode)
    conversations = conversations_query.limit(history_query_limit).all()
    top = rank_conversations(conversations, query, limit=limit)
    memories, mem_sources = _memory_entries(top, "Prior advisor conversation (retrieved)")
    sources.extend(mem_sources)
    return {"authoritative_profile": profile_facts, "retrieved_memories": memories}, sources
