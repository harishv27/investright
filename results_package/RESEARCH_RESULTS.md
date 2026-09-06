# InvestRight — Reproduced Research Results

This document reports results freshly regenerated from the actual InvestRight
codebase (not re-typed from the paper), so every number here is independently
verifiable by re-running the scripts listed under each section. All scripts
live in `backend/scripts/` and require no API key or network access.

Generated: 2026-09-06. Seed: 7 (synthetic evaluation), 42 (risk calibration).

---

## 1. Application verification (is the app "best working"?)

| Check | Result |
|---|---|
| Backend dependency install (Linux, Python 3.12) | Clean install, no conflicts |
| Backend test suite (`pytest tests/ -q`) | **11 / 11 passed** |
| Backend compiles (`compileall app`) | OK, no syntax/import errors |
| Live API smoke test | signup → profile → risk-assessment → dashboard all returned correct, internally-consistent results |
| Capacity guardrail, live-tested | Willingness "Aggressive" + capacity "Resilient" correctly downgraded to decision category "Moderate", exactly per the documented rule |
| Frontend dependency install (Linux, Node 22) | Clean install |
| Frontend production build (`npm run build`) | Succeeded, 226 KB JS / 21 KB CSS bundle |
| Frontend lint (`oxlint`) | 0 errors (fixed 1 of 2 pre-existing warnings; the remaining one is a stylistic React-effect note, not a defect) |

**Bug fixed:** `frontend/src/api/client.js` had an empty, unused catch-block
parameter flagged by the linter; replaced with a documented empty catch.

No functional defects were found in the deterministic analytics, risk
scoring, capacity guardrail, or recommendation-matching code paths.

---

## 2. Table IV — Functional validation (synthetic N=240 profiles)

Reproduced with `backend/scripts/run_synthetic_evaluation.py`, using the
**same production functions** (`app/analytics.py`, `app/risk.py`,
`app/recommendation.py`) that the live API calls — not a re-implementation.

### 2a. Using the paper's original illustrative bands (44% / 72%)

| Test | Result |
|---|---|
| Profiles evaluated | 240 |
| Independent recompute mismatches | 0 / 240 |
| Profiles with negative savings | 0 / 240 |
| Mean savings rate | 38.0% |

This confirms, on a freshly drawn random sample (different seed from the
paper's), the same finding the paper reports: **0 discrepancies between
independently recomputed and system-reported savings rates.**

### 2b. Using the calibrated bands (57.5% / 62.5%, from `risk_calibration.py`)

| Test | Result |
|---|---|
| Profiles evaluated | 240 |
| Independent recompute mismatches | 0 / 240 |
| Profiles with negative savings | 0 / 240 |
| Mean savings rate | 38.0% |

Financial-analytics correctness is unaffected by which risk bands are
active, as expected — the two layers are independent.

---

## 3. Fig. 2 — Risk category distribution (N=240)

### Original bands (paper's reported experiment)

| Risk Category | Profiles | % |
|---|---|---|
| Conservative | 13 | 5.4% |
| Moderate | 199 | 82.9% |
| Aggressive | 28 | 11.7% |

This **matches the paper almost exactly** (paper: 5.4% / 80.8% / 13.8%,
this run: 5.4% / 82.9% / 11.7% — the small difference is expected sampling
noise from a different random seed on the same uniform-random methodology).
It reproduces the paper's central diagnostic finding: **the 44%/72% cut
points concentrate roughly 4 in 5 profiles in the Moderate band.**

### Calibrated bands (this project's proposed fix)

| Risk Category | Profiles | % |
|---|---|---|
| Conservative | 128 | 53.3% |
| Moderate | 30 | 12.5% |
| Aggressive | 82 | 34.2% |

**Honest finding, not previously reported this way:** the calibrated bands
were fit to a *Beta(2.5, 2.5)-shaped* reference population (see
`RESULTS.md`), which approximates realistic, centrally-clustered survey
responses. Against the *uniform*-random population used in the paper's own
synthetic test, those same bands **overcorrect** — they now over-populate
Conservative (53.3%) rather than balancing all three bands. This is not a
contradiction; it demonstrates that a calibration is only as good as how
well its reference population matches the population it will be applied to
in production. The paper's Limitations section already flags this
(Section VII: "risk-category boundaries were illustrative and require
calibration against a validated instrument") — this result adds concrete
evidence for that claim and is a good candidate addition to a revised
Section V-C or VII.

See `figures/fig3_band_calibration_effect.png` for a side-by-side chart.

---

## 4. Table V — Recommended investment category distribution (N=240)

### Original bands

| Recommended Category | Profiles | % |
|---|---|---|
| Balanced Advantage / Index Funds | 153 | 63.8% |
| Balanced Hybrid Funds | 46 | 19.2% |
| Multi-Cap & Growth Equity Funds | 22 | 9.2% |
| Conservative Hybrid / Debt Funds | 11 | 4.6% |
| Large-Cap Equity Funds | 6 | 2.5% |
| Liquid Funds & Fixed Deposits | 2 | 0.8% |

This reproduces the same qualitative pattern as the paper's Table V (dominated
by "Balanced Advantage / Index Funds" because most profiles land in Moderate
+ long horizon), with minor count differences from sampling noise.

### Calibrated bands

| Recommended Category | Profiles | % |
|---|---|---|
| Conservative Hybrid / Debt Funds | 102 | 42.5% |
| Multi-Cap & Growth Equity Funds | 62 | 25.8% |
| Liquid Funds & Fixed Deposits | 26 | 10.8% |
| Balanced Advantage / Index Funds | 22 | 9.2% |
| Large-Cap Equity Funds | 20 | 8.3% |
| Balanced Hybrid Funds | 8 | 3.3% |

The recommendation mix shifts to match the new risk distribution — this is
expected and shows the lookup-table logic (Table II in the paper) responding
correctly to the upstream risk classification.

---

## 5. Retrieval experiment (lexical_rag vs. full_history vs. baselines)

Reproduced with `backend/scripts/run_retrieval_experiment.py`
(`app/retrieval_eval.py`), offline, no LLM call required.

| Metric | lexical_rag | most_recent_k | full_history |
|---|---|---|---|
| Precision@4 | **0.99** | 0.20 | n/a (attaches everything) |
| Context size attached (chars, 100-conv. history) | **456** | – | 11,123 (24× more) |
| Context-assembly latency (ms, 500-conv. history) | 3.67 ms | – | 0.0016 ms (no ranking work) |
| Stale items surfaced (of 10 seeded) | **0 / 10** | 0 / 10 | 10 / 10 (all of it) |

Matches the paper's reported figures within expected run-to-run variance
(latency is hardware-dependent; precision, context size, and staleness
counts are deterministic and match exactly).

---

## 6. Risk-band calibration parameters

| Parameter | Original | Calibrated |
|---|---|---|
| Lower cut | 44% of max score | 57.5% of max score |
| Upper cut | 72% of max score | 62.5% of max score |
| Methodology | Illustrative (unstated justification) | Beta(2.5,2.5)-sampled reference population (n=20,000, seed=42), tertile split at 33%/67% |

Reproduced with `backend/scripts/calibrate_risk_thresholds.py`.

---

## 7. Technology stack (Table III)

| Layer | Technology |
|---|---|
| Frontend | React 19 (Vite 8) |
| Backend / API | Python 3.13, FastAPI 0.115 |
| Database | SQLite (dev) / PostgreSQL (prod-ready via SQLAlchemy 2.0) |
| Auth | JWT (python-jose), bcrypt/passlib password hashing |
| Data processing | Pure Python deterministic modules (analytics.py, risk.py, capacity.py, recommendation.py) |
| OCR / document extraction | pypdf, pytesseract, Pillow |
| Agent / LLM | Groq-hosted LLM, function calling |
| Testing | pytest (11/11 backend tests passing) |

---

## 8. Suggested next steps for the paper / thesis

1. **Add the band-calibration overcorrection finding (Section 3 above)** to
   Section V-C or VII — it's a genuinely new, reproducible result not yet in
   the paper and strengthens the "calibration must match the deployment
   population" argument.
2. **Run `scripts/run_rag_experiment.py`** with a real `GROQ_API_KEY` to get
   the LLM-dependent metrics (unsupported-number rate, faithfulness,
   latency, token cost) — this is written and ready but was never executed
   because the original build environment had no network access to Groq.
3. **Run `recalibrate_from_samples()`** once real (anonymized) questionnaire
   responses exist, and re-run Section 2/3 above against those bands for a
   third, "real-population" comparison column.
4. Proceed with the planned human-subject Likert evaluation (Section V-D of
   the paper) — nothing in this codebase currently automates that; it needs
   a separate study protocol and reviewer recruitment.

---

## File index

```
results_package/
├── RESEARCH_RESULTS.md              <- this file
├── figures/
│   ├── fig2_risk_distribution_original_bands.png
│   ├── fig2b_risk_distribution_calibrated_bands.png
│   ├── fig3_band_calibration_effect.png
│   ├── fig4_retrieval_comparison.png
│   ├── fig_recommendation_distribution_original.png
│   └── fig_recommendation_distribution_calibrated.png
├── tables/                          <- every table above, as .md and .csv
├── raw_data/
│   ├── profiles_raw.json            <- the 240 generated synthetic profiles
│   ├── original_bands_44_72_summary.json
│   ├── original_bands_44_72_per_profile.csv
│   ├── calibrated_bands_summary.json
│   ├── calibrated_bands_per_profile.csv
│   └── retrieval_experiment_results.json
└── scripts/                         <- the exact scripts used to produce everything above
    ├── run_synthetic_evaluation.py
    ├── generate_figures.py
    ├── generate_tables.py
    ├── calibrate_risk_thresholds.py
    └── run_retrieval_experiment.py
```
