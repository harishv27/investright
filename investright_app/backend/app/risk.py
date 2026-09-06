"""
Risk Assessment Module (paper Section 3.4).

Score bands are loaded from a calibrated reference population (see
`app/risk_calibration.py`) rather than fixed at arbitrary percentages. Cut
points are expressed as a percentage of the maximum attainable score so they
remain valid if the number of questionnaire items changes. Run
`python -m app.risk_calibration` to (re)generate `risk_bands.json`; if it
hasn't been generated yet, `load_bands()` falls back to the original
illustrative 44%/72% split so behaviour never breaks silently.
"""

from app.risk_calibration import load_bands

_BANDS = load_bands()


def score_risk(responses: list[int]) -> dict:
    score = sum(responses)
    max_score = len(responses) * 5

    lower_cut = max_score * _BANDS["lower_pct"]
    upper_cut = max_score * _BANDS["upper_pct"]

    if score <= lower_cut:
        category = "Conservative"
    elif score <= upper_cut:
        category = "Moderate"
    else:
        category = "Aggressive"

    return {
        "score": score,
        "max_score": max_score,
        "risk_category": category,
        "band_lower_pct": _BANDS["lower_pct"],
        "band_upper_pct": _BANDS["upper_pct"],
        "band_methodology": _BANDS.get("methodology"),
    }
