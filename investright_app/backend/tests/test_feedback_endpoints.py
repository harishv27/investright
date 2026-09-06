from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_submit_and_get_feedbacks():
    # Submit feedback
    payload = {
        "overall_rating": 5,
        "voice_feature_rating": 4,
        "text_chat_rating": 5,
        "ai_advisor_rating": 5,
        "user_friendly_rating": 5,
        "document_extraction_rating": 4,
        "multilingual_rating": 5,
        "nps_score": 10,
        "most_valuable_feature": "Tamil / Regional Voice Input",
        "suggestions": "Phenomenal tool, especially the grounded mutual fund allocations.",
    }
    post_res = client.post("/api/feedback", json=payload)
    assert post_res.status_code == 200
    created = post_res.json()
    assert created["overall_rating"] == 5
    assert created["nps_score"] == 10

    # Get summary
    sum_res = client.get("/api/feedback/summary")
    assert sum_res.status_code == 200
    summary = sum_res.json()
    assert summary["total_feedbacks"] >= 1
    assert summary["average_overall"] > 0

    # Get all feedbacks list (for admin)
    list_res = client.get("/api/feedback")
    assert list_res.status_code == 200
    items = list_res.json()
    assert isinstance(items, list)
    assert len(items) >= 1
