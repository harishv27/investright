import zipfile
import io
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_benchmark_5_users():
    res = client.get("/api/evaluation/benchmark-5-users")
    assert res.status_code == 200
    data = res.json()
    assert data["n_users"] == 5
    assert "mean_latency_sec" in data
    assert "p50_latency_sec" in data
    assert "users" in data
    assert len(data["users"]) == 5


def test_re_evaluate_benchmark():
    res = client.post("/api/evaluation/re-evaluate")
    assert res.status_code == 200
    data = res.json()
    assert data["n_users"] == 5
    assert data["p50_latency_sec"] > 0
    assert data["mean_tokens"] > 0


def test_paper_latex():
    res = client.get("/api/evaluation/paper-latex")
    assert res.status_code == 200
    data = res.json()
    assert "begin{table" in data["latex"]
    assert "Priya Sharma" in data["latex"]


def test_export_zip():
    res = client.get("/api/evaluation/export-zip")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/zip"
    zf = zipfile.ZipFile(io.BytesIO(res.content))
    namelist = zf.namelist()
    assert "benchmark_summary.json" in namelist
    assert "benchmark_5_users_table.csv" in namelist
    assert "paper_table.tex" in namelist
    assert "lexical_rag_comparison.csv" in namelist
    assert "user_feedbacks.csv" in namelist
    assert "README_RESEARCH_EVALUATION.md" in namelist
