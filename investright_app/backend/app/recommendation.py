"""
Investment Category Matching Module (paper Section 3.5 / Table 4).

A fixed, explicit lookup table -- deliberately not left to the LLM,
so results are consistent and independently verifiable.
"""

INVESTMENT_MATCH_TABLE = {
    ("Conservative", "short"): (
        "Liquid Funds & Fixed Deposits",
        "Prioritizes capital safety and easy access to cash over a short window.",
    ),
    ("Conservative", "long"): (
        "Conservative Hybrid / Debt Funds",
        "Preserves capital while allowing modest, steady long-term growth.",
    ),
    ("Moderate", "short"): (
        "Balanced Hybrid Funds",
        "Mixes equity and debt to manage volatility over a shorter window.",
    ),
    ("Moderate", "long"): (
        "Balanced Advantage / Index Funds",
        "Balances growth and stability, suited to a longer runway.",
    ),
    ("Aggressive", "short"): (
        "Large-Cap Equity Funds",
        "Growth-oriented, tempered given the shorter time to recover from dips.",
    ),
    ("Aggressive", "long"): (
        "Multi-Cap & Growth Equity Funds",
        "Maximizes long-term growth potential, tolerating higher short-term volatility.",
    ),
}


def horizon_bucket(horizon_years: int) -> str:
    return "short" if horizon_years < 5 else "long"


def match_investment_category(risk_category: str, horizon_years: int) -> dict:
    bucket = horizon_bucket(horizon_years)
    category, rationale = INVESTMENT_MATCH_TABLE[(risk_category, bucket)]
    return {
        "recommended_category": category,
        "rationale": rationale,
        "horizon_bucket": bucket,
    }
