"""Unit tests for the calibrated risk-band logic. Run with:
    cd backend && python -m pytest tests/ -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.risk import score_risk
from app.risk_calibration import recalibrate, load_bands


def test_bands_load():
    bands = load_bands()
    assert "lower_pct" in bands and "upper_pct" in bands
    assert 0 < bands["lower_pct"] < bands["upper_pct"] < 1


def test_score_risk_monotonic():
    low = score_risk([1] * 8)
    mid = score_risk([3] * 8)
    high = score_risk([5] * 8)
    assert low["score"] < mid["score"] < high["score"]
    order = {"Conservative": 0, "Moderate": 1, "Aggressive": 2}
    assert order[low["risk_category"]] <= order[mid["risk_category"]] <= order[high["risk_category"]]


def test_score_risk_bounds():
    result = score_risk([1, 2, 3, 4, 5, 1, 2, 3])
    assert result["max_score"] == 40
    assert result["risk_category"] in ("Conservative", "Moderate", "Aggressive")


def test_recalibrate_is_deterministic_for_fixed_seed():
    b1 = recalibrate(seed=99, n_samples=2000)
    b2 = recalibrate(seed=99, n_samples=2000)
    assert b1["lower_pct"] == b2["lower_pct"]
    assert b1["upper_pct"] == b2["upper_pct"]
    # restore the project's canonical calibration afterwards
    recalibrate()
