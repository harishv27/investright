"""
Synthetic dataset evaluation — reproduces paper Section V
(Experimental Evaluation) using the production analytics, risk, and
recommendation modules directly, so the reported numbers are guaranteed
to match what the deployed backend would compute for the same inputs.

Generates, for N=240 synthetic profiles (paper Section V-A sampling ranges):

  1. Table IV — Functional validation (independent-recompute check)
  2. Fig. 2   — Risk-category distribution (bar chart, PNG)
  3. Table V  — Recommended-investment-category distribution

Run twice: once with the paper's original illustrative 44%/72% risk bands
(to reproduce the exact experiment described in the paper), and once with
the calibrated bands from risk_calibration.py (to show the effect of
calibration on the same synthetic population). Both result sets are
written to backend/scripts/synthetic_evaluation_results/.

No network access or API key required. Fully deterministic given the seed.
"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.analytics import calculate_financials
from app.recommendation import match_investment_category

N_PROFILES = 240
N_QUESTIONS = 8
SEED = 7

OUT_DIR = os.path.join(os.path.dirname(__file__), "synthetic_evaluation_results")
os.makedirs(OUT_DIR, exist_ok=True)


def generate_profiles(n=N_PROFILES, seed=SEED):
    """Sampling ranges exactly as described in paper Section V-A."""
    rng = random.Random(seed)
    goals = ["retirement", "wealth_growth", "home_purchase", "education"]
    profiles = []
    for i in range(n):
        age = rng.randint(22, 58)
        income = rng.uniform(20000, 180000)
        expense_frac = rng.uniform(0.35, 0.90)
        expenses = income * expense_frac
        residual_savings = income - expenses
        planned_frac = rng.uniform(0.10, 0.80)
        planned_investment = max(0.0, residual_savings * planned_frac)
        horizon_years = rng.randint(1, 20)
        goal = rng.choice(goals)
        responses = [rng.randint(1, 5) for _ in range(N_QUESTIONS)]
        profiles.append({
            "id": i + 1,
            "age": age,
            "income": round(income, 2),
            "expenses": round(expenses, 2),
            "planned_investment": round(planned_investment, 2),
            "horizon_years": horizon_years,
            "goal": goal,
            "risk_responses": responses,
        })
    return profiles


def score_risk_with_bands(responses, lower_pct, upper_pct):
    score = sum(responses)
    max_score = len(responses) * 5
    lower_cut = max_score * lower_pct
    upper_cut = max_score * upper_pct
    if score <= lower_cut:
        category = "Conservative"
    elif score <= upper_cut:
        category = "Moderate"
    else:
        category = "Aggressive"
    return score, max_score, category


def independent_recompute(income, expenses):
    """Recomputation done independently of app.analytics, for the
    functional-consistency check (Table IV)."""
    savings = income - expenses
    savings_rate = round((savings / income) * 100, 1) if income else 0.0
    return savings, savings_rate


def run_experiment(profiles, lower_pct, upper_pct, label):
    mismatches = 0
    negative_savings = 0
    savings_rates = []
    risk_counter = {"Conservative": 0, "Moderate": 0, "Aggressive": 0}
    reco_counter = {}
    per_profile_rows = []

    for p in profiles:
        fin = calculate_financials(p["income"], p["expenses"], p["planned_investment"])

        indep_savings, indep_rate = independent_recompute(p["income"], p["expenses"])
        if abs(indep_rate - fin["savings_rate_pct"]) > 1e-6:
            mismatches += 1
        if fin["monthly_savings"] < 0:
            negative_savings += 1
        savings_rates.append(fin["savings_rate_pct"])

        score, max_score, risk_category = score_risk_with_bands(
            p["risk_responses"], lower_pct, upper_pct
        )
        risk_counter[risk_category] += 1

        reco = match_investment_category(risk_category, p["horizon_years"])
        reco_counter[reco["recommended_category"]] = (
            reco_counter.get(reco["recommended_category"], 0) + 1
        )

        per_profile_rows.append({
            "id": p["id"],
            "income": p["income"],
            "expenses": p["expenses"],
            "monthly_savings": fin["monthly_savings"],
            "savings_rate_pct": fin["savings_rate_pct"],
            "expense_ratio_pct": fin["expense_ratio_pct"],
            "risk_score": score,
            "max_score": max_score,
            "risk_category": risk_category,
            "horizon_years": p["horizon_years"],
            "recommended_category": reco["recommended_category"],
        })

    n = len(profiles)
    mean_savings_rate = round(sum(savings_rates) / n, 1)

    table_iv = {
        "profiles_evaluated": n,
        "independent_recompute_mismatches": f"{mismatches} / {n}",
        "profiles_with_negative_savings": f"{negative_savings} / {n}",
        "mean_savings_rate_pct": mean_savings_rate,
    }

    risk_distribution = {
        cat: {"count": count, "pct": round(100 * count / n, 1)}
        for cat, count in risk_counter.items()
    }

    reco_distribution = sorted(
        (
            {"category": cat, "count": count, "pct": round(100 * count / n, 1)}
            for cat, count in reco_counter.items()
        ),
        key=lambda r: -r["count"],
    )

    result = {
        "label": label,
        "bands": {"lower_pct": lower_pct, "upper_pct": upper_pct},
        "n_profiles": n,
        "n_questions": N_QUESTIONS,
        "seed": SEED,
        "table_iv_functional_validation": table_iv,
        "fig2_risk_category_distribution": risk_distribution,
        "table_v_recommended_category_distribution": reco_distribution,
    }

    with open(os.path.join(OUT_DIR, f"{label}_summary.json"), "w") as f:
        json.dump(result, f, indent=2)

    with open(os.path.join(OUT_DIR, f"{label}_per_profile.csv"), "w") as f:
        headers = list(per_profile_rows[0].keys())
        f.write(",".join(headers) + "\n")
        for row in per_profile_rows:
            f.write(",".join(str(row[h]) for h in headers) + "\n")

    return result


def main():
    profiles = generate_profiles()

    with open(os.path.join(OUT_DIR, "profiles_raw.json"), "w") as f:
        json.dump(profiles, f, indent=2)

    original = run_experiment(profiles, 0.44, 0.72, "original_bands_44_72")
    try:
        from app.risk_calibration import load_bands
        bands = load_bands()
        calibrated = run_experiment(
            profiles, bands["lower_pct"], bands["upper_pct"], "calibrated_bands"
        )
    except Exception as e:
        calibrated = None
        print(f"Skipped calibrated-band run: {e}")

    print(json.dumps(original, indent=2))
    if calibrated:
        print(json.dumps(calibrated, indent=2))
    print(f"\nWritten to {OUT_DIR}/")


if __name__ == "__main__":
    main()
