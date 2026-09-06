"""
Financial Analytics Module.

Pure, deterministic functions. No AI involvement -- these are the
"ground truth" calculations described in the paper's Section 3.3.
"""


def calculate_financials(income: float, expenses: float, planned_investment: float) -> dict:
    savings = income - expenses
    savings_rate = round((savings / income) * 100, 1) if income else 0.0
    expense_ratio = round((expenses / income) * 100, 1) if income else 0.0
    investment_capacity = round(max(0.0, savings - planned_investment), 2)

    return {
        "monthly_savings": round(savings, 2),
        "savings_rate_pct": savings_rate,
        "expense_ratio_pct": expense_ratio,
        "investment_capacity": investment_capacity,
    }
