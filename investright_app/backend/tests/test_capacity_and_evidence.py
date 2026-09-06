import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.capacity import adjust_risk_for_capacity, calculate_capacity
from app.media_extraction import extract_candidates


def test_capacity_scores_emergency_buffer_and_surplus():
    result = calculate_capacity(100000, 50000, 300000, 10000)
    assert result["emergency_months"] == 6.0
    assert result["capacity_category"] == "Strong"
    assert result["capacity_score"] > 70


def test_capacity_guardrail_reduces_aggressive_willingness_when_limited():
    category, explanation = adjust_risk_for_capacity("Aggressive", "Limited")
    assert category == "Conservative"
    assert "capacity" in explanation.lower()


def test_capacity_does_not_override_conservative_willingness():
    category, _ = adjust_risk_for_capacity("Conservative", "Strong")
    assert category == "Conservative"


def test_payslip_candidates_distinguish_net_pay_and_deductions():
    candidates = extract_candidates("Total Earnings 11600 Total Deductions 2100 Net Pay 9500")
    assert candidates["income"] == 9500
    assert candidates["gross_earnings"] == 11600
    assert candidates["net_pay"] == 9500
    assert candidates["deductions"] == 2100