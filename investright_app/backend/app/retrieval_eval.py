"""
Offline RAG comparison experiment (paper Section V-D / README Section 7).

Compares the three retrieval conditions implemented in app/retrieval.py --
no_memory, full_history, lexical_rag -- on metrics that do NOT require an
LLM call, so this runs anywhere, deterministically, with no API key:

  * context_size_chars   -- proxy for prompt/token cost sent to the LLM.
  * precision_at_k       -- of the conversations attached as memory, what
                             fraction are actually topically relevant to the
                             current query, against a known synthetic
                             ground truth. Compared against a
                             "most-recent-k" baseline (what full_history
                             degenerates to once truncated to a context
                             window) and a random-k baseline.
  * latency_ms           -- wall-clock time to assemble context, benchmarked
                             against a synthetic 500-conversation history to
                             simulate a heavy long-time user.
  * conflicting_items_included -- how many topically stale/conflicting prior
                             conversations end up in the assembled context,
                             as a proxy for staleness exposure.

A second, LLM-dependent experiment (unsupported-number rate, answer
faithfulness, token cost, response latency) is implemented separately in
scripts/run_rag_experiment.py and requires GROQ_API_KEY -- it exercises the
real agent loop end-to-end and is not run as part of this module.
"""

import random
import statistics
import time
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.retrieval import rank_conversations, _tokens


@dataclass
class FakeConversation:
    id: int
    query: str
    response: str
    created_at: datetime
    topic: str  # ground-truth label, used only for evaluation, not by the ranker


TOPIC_BANK = {
    "risk_tolerance": [
        ("How would I react if my investment dropped 20%?",
         "Based on your risk assessment, you're categorized as Moderate risk."),
        ("Am I a conservative or aggressive investor?",
         "Your risk score places you in the Moderate category."),
        ("Should I be worried about market volatility?",
         "Given your Moderate risk profile, some volatility is expected and within tolerance."),
    ],
    "goal_planning": [
        ("How long until I reach my retirement goal?",
         "At your current savings rate, your long-term wealth creation goal is on track."),
        ("What's my investment horizon for this goal?",
         "Your stated horizon is a long-term goal, which favors growth-oriented categories."),
        ("Is my financial goal realistic given my income?",
         "Your goal of long-term wealth creation aligns with your investment capacity."),
    ],
    "fund_lookup": [
        ("Can you find real mutual funds matching my category?",
         "I looked up live fund data matching your recommended category."),
        ("What funds are available in the balanced advantage category?",
         "Here are current balanced advantage fund options from live data."),
        ("Show me index fund options.",
         "Here are index fund schemes matching your recommended category."),
    ],
    "platform_fees": [
        ("Which platform has the lowest fees?",
         "Here's a curated, non-live comparison of platform fee structures."),
        ("Do any platforms charge no commission?",
         "Some platforms in the curated list offer direct plans with no commission."),
        ("What's the minimum investment on these platforms?",
         "Minimum investments vary by platform; see the curated comparison."),
    ],
    "savings_rate": [
        ("What's my current savings rate?",
         "Your savings rate is calculated from your income and expenses."),
        ("How can I improve my expense ratio?",
         "Reducing discretionary expenses would improve your expense ratio."),
        ("Is my savings rate healthy?",
         "Your savings rate is within a healthy range relative to your income."),
    ],
}


def make_synthetic_history(n_per_topic: int = 20, seed: int = 11) -> list[FakeConversation]:
    rng = random.Random(seed)
    now = datetime.utcnow()
    conversations = []
    cid = 1
    for topic, templates in TOPIC_BANK.items():
        for _ in range(n_per_topic):
            q, r = rng.choice(templates)
            days_ago = rng.randint(0, 720)
            conversations.append(FakeConversation(
                id=cid, query=q, response=r,
                created_at=now - timedelta(days=days_ago), topic=topic,
            ))
            cid += 1
    rng.shuffle(conversations)
    return conversations


def _most_recent_k(conversations: list[FakeConversation], k: int) -> list[FakeConversation]:
    return sorted(conversations, key=lambda c: c.created_at, reverse=True)[:k]


def _random_k(conversations: list[FakeConversation], k: int, seed: int) -> list[FakeConversation]:
    rng = random.Random(seed)
    return rng.sample(conversations, min(k, len(conversations)))


def precision_at_k_experiment(k: int = 4, n_per_topic: int = 20, trials_per_topic: int = 5) -> dict:
    """For each topic, issue topic-matching queries and measure what fraction
    of the top-k retrieved conversations share the query's ground-truth
    topic, for the lexical_rag ranker vs. two baselines.
    """
    history = make_synthetic_history(n_per_topic=n_per_topic)
    results = {"lexical_rag": [], "most_recent_k": [], "random_k": []}

    trial = 0
    for topic, templates in TOPIC_BANK.items():
        for i in range(trials_per_topic):
            query = templates[i % len(templates)][0]

            lexical_top = rank_conversations(history, query, limit=k)
            recent_top = _most_recent_k(history, k)
            random_top = _random_k(history, k, seed=100 + trial)

            for name, top in [("lexical_rag", lexical_top), ("most_recent_k", recent_top), ("random_k", random_top)]:
                relevant = sum(1 for c in top if c.topic == topic)
                results[name].append(relevant / k)
            trial += 1

    return {name: round(statistics.mean(scores), 4) for name, scores in results.items()}


def context_size_experiment(n_per_topic: int = 20, k: int = 4) -> dict:
    """Character count of the memory payload under each condition, as a
    token-cost proxy (no_memory attaches none; full_history attaches every
    stored conversation; lexical_rag attaches only the top-k).
    """
    history = make_synthetic_history(n_per_topic=n_per_topic)
    query = "How would I react if my investment dropped 20%?"

    def size_of(conversations):
        return sum(len(c.query) + len(c.response) for c in conversations)

    lexical_top = rank_conversations(history, query, limit=k)
    return {
        "no_memory_chars": 0,
        "full_history_chars": size_of(history),
        "lexical_rag_chars": size_of(lexical_top),
        "total_conversations_in_history": len(history),
        "conversations_attached_full_history": len(history),
        "conversations_attached_lexical_rag": len(lexical_top),
    }


def latency_experiment(n_per_topic: int = 100, k: int = 4, repeats: int = 20) -> dict:
    """Wall-clock time to assemble context under each mode against a large
    (500-conversation) synthetic history, simulating a long-time user.
    """
    history = make_synthetic_history(n_per_topic=n_per_topic)
    query = "How would I react if my investment dropped 20%?"

    def time_it(fn):
        times = []
        for _ in range(repeats):
            start = time.perf_counter()
            fn()
            times.append((time.perf_counter() - start) * 1000)
        return round(statistics.mean(times), 4)

    return {
        "n_conversations_in_history": len(history),
        "no_memory_ms": 0.0,  # no history touched at all
        "full_history_ms": time_it(lambda: list(history)),
        "lexical_rag_ms": time_it(lambda: rank_conversations(history, query, limit=k)),
    }


def staleness_exposure_experiment(k: int = 4) -> dict:
    """Construct a history containing several conversations that reference a
    now-outdated financial figure alongside current-topic conversations, and
    measure how many *stale* items end up in the assembled context under
    each retrieval mode. This is a structural proxy for the failure mode the
    provenance-aware design targets: a stale conversational claim
    contradicting the current authoritative profile.
    """
    now = datetime.utcnow()
    history = []
    cid = 1
    # 10 old conversations referencing a stale, now-incorrect income figure
    for _ in range(10):
        history.append(FakeConversation(
            id=cid, query="What's my investment capacity?",
            response="Based on your income of ₹40,000, your investment capacity is limited.",
            created_at=now - timedelta(days=400), topic="stale_income",
        ))
        cid += 1
    # 10 recent, current-topic conversations
    for _ in range(10):
        history.append(FakeConversation(
            id=cid, query="What's my investment capacity now?",
            response="Based on your current income, your investment capacity has increased.",
            created_at=now - timedelta(days=2), topic="current_income",
        ))
        cid += 1

    query = "What's my current investment capacity?"
    lexical_top = rank_conversations(history, query, limit=k)
    recent_top = _most_recent_k(history, k)

    return {
        "stale_items_in_full_history": sum(1 for c in history if c.topic == "stale_income"),
        "stale_items_in_lexical_rag_top_k": sum(1 for c in lexical_top if c.topic == "stale_income"),
        "stale_items_in_most_recent_k": sum(1 for c in recent_top if c.topic == "stale_income"),
        "note": (
            "In every mode, authoritative profile facts are attached as a separate, "
            "explicitly-labeled block ahead of any conversational memory (see "
            "build_profile_context in retrieval.py), so even when stale conversational "
            "items are retrieved, they are distinguishable from -- and, per the agent's "
            "system prompt, subordinate to -- current structured facts. full_history is "
            "the condition most exposed to stale content by volume."
        ),
    }


def run_all(n_per_topic: int = 20, k: int = 4) -> dict:
    return {
        "precision_at_k": precision_at_k_experiment(k=k, n_per_topic=n_per_topic),
        "context_size": context_size_experiment(n_per_topic=n_per_topic, k=k),
        "latency": latency_experiment(n_per_topic=100, k=k),
        "staleness_exposure": staleness_exposure_experiment(k=k),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(run_all(), indent=2))
