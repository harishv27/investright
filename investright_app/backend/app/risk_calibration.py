"""
Risk-band calibration.

The original implementation fixed the Conservative/Moderate/Aggressive cut
points at 44% and 72% of the maximum questionnaire score with no stated
justification. This module replaces that with cut points derived from a
reference population, and keeps the derivation re-runnable so the bands can
be refreshed once real user response data is available.

Methodology
-----------
Real risk-questionnaire responses are not uniform across 1-5; respondents
cluster around the middle of the scale, which is consistent with findings in
the robo-advisory literature (e.g. Boreiko & Massarotti, 2020, who report
that robo-advised portfolios are systematically conservative relative to
investors' stated risk tolerance, and So et al., 2021, who find no
standardized weighting scheme across common questionnaire item types). We
approximate this clustering with a discretized symmetric Beta(2.5, 2.5)
distribution mapped onto {1..5} -- bell-shaped and centered, rather than
flat -- sample a large reference population's total scores, and set the
lower/upper cut points at the population tertiles (33rd / 67th percentile).
A tertile split is the convention used by most three-band robo-advisor
risk-bucket designs and gives each band a comparable base rate on a
realistic population, instead of letting the split be an artifact of where
the cut points happen to fall.

This is still a synthetic calibration, not a validated psychometric
instrument. `recalibrate()` should be re-run against real, anonymized
response data (see `recalibrate_from_samples`) as soon as it is available,
and the resulting bands should ideally be reviewed by someone with
psychometric or financial-advisory domain expertise before being treated as
authoritative.
"""

import json
import os
import random
from statistics import quantiles

DEFAULT_N_QUESTIONS = 8
BANDS_PATH = os.path.join(os.path.dirname(__file__), "risk_bands.json")

# Fallback used only if risk_bands.json is missing and calibration has never
# been run -- kept equal to the original illustrative draft values so
# behaviour doesn't change silently for anyone who skips calibration.
_FALLBACK_BANDS = {
    "lower_pct": 0.44,
    "upper_pct": 0.72,
    "methodology": "illustrative default (uncalibrated -- run "
                   "`python -m app.risk_calibration` to calibrate)",
}


def _sample_beta_1_5(rng: random.Random) -> int:
    """One synthetic questionnaire-item response, bell-shaped over {1..5}."""
    x = rng.betavariate(2.5, 2.5)  # in [0, 1], symmetric, centered at 0.5
    return min(5, max(1, int(round(1 + x * 4))))


def recalibrate(
    n_questions: int = DEFAULT_N_QUESTIONS,
    n_samples: int = 20000,
    seed: int = 42,
    target_split: tuple[float, float] = (1 / 3, 2 / 3),
) -> dict:
    """Derive and persist cut points from a synthetic reference population.

    Returns the bands dict and writes it to risk_bands.json so `load_bands()`
    picks it up without re-running the simulation on every import.
    """
    rng = random.Random(seed)
    scores = [
        sum(_sample_beta_1_5(rng) for _ in range(n_questions))
        for _ in range(n_samples)
    ]
    scores.sort()
    qs = quantiles(scores, n=100)
    q_low, q_high = target_split
    lower_cut_score = qs[max(0, int(round(q_low * 100)) - 1)]
    upper_cut_score = qs[max(0, int(round(q_high * 100)) - 1)]
    max_score = n_questions * 5

    bands = {
        "n_questions_reference": n_questions,
        "lower_pct": round(lower_cut_score / max_score, 4),
        "upper_pct": round(upper_cut_score / max_score, 4),
        "methodology": (
            f"Beta(2.5,2.5)-sampled reference population (n={n_samples}, "
            f"seed={seed}), tertile split at {target_split[0]:.0%}/"
            f"{target_split[1]:.0%}. See app/risk_calibration.py for the "
            f"full rationale."
        ),
        "n_samples": n_samples,
        "seed": seed,
        "target_split": list(target_split),
    }
    with open(BANDS_PATH, "w") as f:
        json.dump(bands, f, indent=2)
    return bands


def recalibrate_from_samples(
    response_sets: list[list[int]],
    target_split: tuple[float, float] = (1 / 3, 2 / 3),
) -> dict:
    """Calibrate from real (anonymized) questionnaire response data.

    `response_sets` is a list of per-user response lists, e.g.
    [[4,3,5,2,4,3,5,4], [2,2,1,3,2,2,1,2], ...]. Use this once real user
    data is available instead of the synthetic Beta-sampled population.
    """
    if not response_sets:
        raise ValueError("response_sets must be non-empty")
    n_questions = len(response_sets[0])
    scores = sorted(sum(r) for r in response_sets)
    qs = quantiles(scores, n=100) if len(scores) >= 100 else scores
    q_low, q_high = target_split
    idx_low = max(0, min(len(qs) - 1, int(round(q_low * (len(qs) - 1)))))
    idx_high = max(0, min(len(qs) - 1, int(round(q_high * (len(qs) - 1)))))
    max_score = n_questions * 5

    bands = {
        "n_questions_reference": n_questions,
        "lower_pct": round(qs[idx_low] / max_score, 4),
        "upper_pct": round(qs[idx_high] / max_score, 4),
        "methodology": f"Calibrated from {len(response_sets)} real response sets "
                        f"(tertile split at {target_split[0]:.0%}/{target_split[1]:.0%}).",
        "n_samples": len(response_sets),
        "target_split": list(target_split),
    }
    with open(BANDS_PATH, "w") as f:
        json.dump(bands, f, indent=2)
    return bands


def load_bands() -> dict:
    if os.path.exists(BANDS_PATH):
        with open(BANDS_PATH) as f:
            return json.load(f)
    return dict(_FALLBACK_BANDS)


if __name__ == "__main__":
    result = recalibrate()
    print(json.dumps(result, indent=2))
