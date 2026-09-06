"""Deterministic financial capacity analysis.

Capacity is distinct from willingness to take investment risk. It describes
the user's observable ability to absorb volatility using income, expenses,
savings, and planned contributions.
"""


def calculate_capacity(income: float, expenses: float, savings: float, planned_investment: float) -> dict:
    if income <= 0:
        raise ValueError("income must be greater than zero")
    if expenses < 0 or savings < 0 or planned_investment < 0:
        raise ValueError("expenses, savings, and planned investment cannot be negative")

    surplus = max(0.0, income - expenses)
    expense_ratio = expenses / income
    emergency_months = savings / expenses if expenses else float("inf")
    contribution_ratio = planned_investment / income

    buffer_score = min(emergency_months / 6, 1) * 45
    surplus_score = min(surplus / income, 0.5) / 0.5 * 35
    contribution_score = min(contribution_ratio / 0.25, 1) * 20
    score = round(max(0, min(100, buffer_score + surplus_score + contribution_score)), 1)

    if score < 40:
        category = "Limited"
        guidance = "Build a larger cash buffer before taking substantial investment risk."
    elif score < 70:
        category = "Resilient"
        guidance = "A balanced approach may be suitable while the emergency buffer grows."
    else:
        category = "Strong"
        guidance = "Your current cash buffer and surplus support a broader investment range."

    return {
        "capacity_score": score,
        "capacity_category": category,
        "emergency_months": round(emergency_months, 1) if emergency_months != float("inf") else None,
        "surplus_inr_per_month": round(surplus, 2),
        "expense_ratio_pct": round(expense_ratio * 100, 1),
        "contribution_ratio_pct": round(contribution_ratio * 100, 1),
        "guidance": guidance,
    }


def adjust_risk_for_capacity(willingness_category: str, capacity_category: str) -> tuple[str, str]:
    """Apply a conservative guardrail when willingness exceeds ability."""
    if capacity_category == "Limited" and willingness_category != "Conservative":
        return "Conservative", "Your financial capacity is currently below your stated risk willingness."
    if capacity_category == "Resilient" and willingness_category == "Aggressive":
        return "Moderate", "Your capacity supports balance, but not the full volatility of an aggressive profile."
    return willingness_category, "Your stated risk willingness is consistent with your current financial capacity."