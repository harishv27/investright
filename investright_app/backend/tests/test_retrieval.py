"""Unit tests for the retrieval layer's pure ranking core and mode contract.
Run with: cd backend && python -m pytest tests/ -v
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.retrieval import rank_conversations, MODES


class FakeConversation:
    def __init__(self, id, query, response, created_at):
        self.id = id
        self.query = query
        self.response = response
        self.created_at = created_at


def test_rank_conversations_prefers_lexical_overlap():
    now = datetime.utcnow()
    convos = [
        FakeConversation(1, "What funds match my category?", "Here are funds.", now - timedelta(days=300)),
        FakeConversation(2, "What's the weather today?", "Unrelated response.", now - timedelta(days=1)),
    ]
    top = rank_conversations(convos, "Can you find funds matching my category?", limit=1, now=now)
    assert top[0].id == 1  # relevant-but-old should outrank recent-but-irrelevant here


def test_rank_conversations_respects_limit():
    now = datetime.utcnow()
    convos = [FakeConversation(i, f"query {i}", f"response {i}", now - timedelta(days=i)) for i in range(10)]
    top = rank_conversations(convos, "query", limit=3, now=now)
    assert len(top) == 3


def test_modes_are_exactly_three():
    assert set(MODES) == {"no_memory", "full_history", "lexical_rag"}
