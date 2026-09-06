# What changed in this update

Two additions, both fully implemented and runnable, plus real result
artifacts already generated and checked into this repo so you don't have to
re-run anything to see the numbers (though you can, and should, once you
change the reference population or add real data).

---

## 1. Risk-threshold recalibration

**Problem:** the original `risk.py` fixed the Conservative/Moderate/Aggressive
cut points at 44% / 72% of the maximum score with no stated justification.
On a synthetic 240-profile test with uniformly random questionnaire
responses, this produced an 82.5% "Moderate" skew — almost everyone got the
same label, which makes the classifier close to useless in practice.

**What was built:**
- `backend/app/risk_calibration.py` — derives cut points from a reference
  population instead of picking them by hand. Response items are sampled
  from a discretized Beta(2.5, 2.5) distribution (bell-shaped, centered —
  approximating the real clustering-around-the-middle behavior reported in
  the robo-advisory literature, e.g. Boreiko & Massarotti 2020) rather than
  a flat uniform distribution, and cut points are set at the 33rd/67th
  percentile of the resulting score distribution (a tertile split, the
  convention used by most three-band robo-advisor designs).
- `backend/app/risk_bands.json` — the generated output, loaded by `risk.py`
  at import time. Regenerate with `python -m scripts.calibrate_risk_thresholds`.
- `recalibrate_from_samples()` — the same logic, but taking real (anonymized)
  user response data instead of the synthetic reference population. Use this
  once you have real users; the synthetic calibration is a reasonable
  starting point, not a substitute for it.
- `backend/tests/test_risk_calibration.py` — unit tests (monotonicity,
  bounds, determinism).

**Real, reproducible before/after result** (240 synthetic profiles, 8
questions each):

| Population | Old bands (0.44 / 0.72) | New calibrated bands (0.575 / 0.625) |
|---|---|---|
| Uniform-random responses | Conservative 6.7% / **Moderate 82.5%** / Aggressive 10.8% | Conservative 49.2% / Moderate 22.1% / Aggressive 28.7% |
| Beta-sampled "realistic" responses | Conservative 0.0% / **Moderate 95.8%** / Aggressive 4.2% | Conservative 42.1% / Moderate 30.8% / Aggressive 27.1% |

On the realistic population the new bands land close to the 33/33/33 target
they were calibrated for. This is still a synthetic calibration — the honest
next step is running `recalibrate_from_samples()` against real user
responses once you have them, ideally reviewed by someone with
psychometric/financial-advisory background.

---

## 2. RAG comparison experiment (no-memory vs. full-history vs. lexical-RAG)

This is split into two parts, matching what can and can't be measured
without calling a real LLM.

### 2a. Offline retrieval-only metrics (implemented AND executed — real numbers)

`backend/app/retrieval_eval.py` + `backend/scripts/run_retrieval_experiment.py`.
No API key needed. Result saved at `backend/scripts/retrieval_experiment_results.json`:

| Metric | lexical_rag | full_history | most_recent_k / random_k baselines |
|---|---|---|---|
| Precision@4 (topic-relevance of retrieved memory) | **0.99** | n/a (attaches everything) | most_recent_k 0.20, random_k 0.19 |
| Context size attached (chars, 100-conversation history) | **456** | 11,123 (24x more) | — |
| Context-assembly latency (500-conversation history) | 2.7 ms | 0.001 ms (no ranking work) | — |
| Stale items surfaced (10 stale-topic items seeded in history) | **0 / 4** | 10 / 10 (all of it) | most_recent_k also 0/4 here (stale items happened to be old) |

Reading this honestly: lexical_rag's precision and context-size wins are
real and reproducible. `full_history` is trivially "faster" to *assemble*
because it does no ranking work at all — the cost it pays instead is a much
larger, unranked, unfiltered context handed to the LLM (24x more characters,
including all the stale content), which is the actual point of the
comparison: full_history isn't slow, it's just unfiltered.

### 2b. LLM-dependent metrics (implemented, NOT executed — needs your API key)

`backend/scripts/run_rag_experiment.py` runs the real `app.agent.run_agent`
loop under each of the three modes and measures unsupported-number rate,
answer faithfulness (does the answer state the correct risk/recommendation
category), latency, and token cost. This requires network access to the
Groq API, which the environment used to build this update did not have —
so this script is fully written and ready to use, but its numbers have not
been generated. Run it yourself with a real `GROQ_API_KEY` set in
`backend/.env`:

```bash
cd backend
python -m scripts.run_rag_experiment
```

Results are written to `backend/scripts/rag_experiment_results.json`.

---

## 3. Evidence-backed capacity guardrail (implemented)

The product now separates risk willingness from financial capacity. The new
`backend/app/capacity.py` module deterministically scores emergency-fund
coverage, monthly surplus, expense ratio, and planned-contribution ratio.
Capacity is classified as `Limited`, `Resilient`, or `Strong`.

The recommendation layer applies a transparent guardrail:

- `Limited` capacity caps non-Conservative willingness at Conservative.
- `Resilient` capacity caps Aggressive willingness at Moderate.
- `Strong` capacity preserves the stated willingness category.

The API returns both the original willingness category and the final
`decision_risk_category`, together with an explanation. This is intentionally
deterministic and inspectable; the LLM does not calculate or override it.

The document workflow now persists each extracted numeric candidate as a
`FinancialEvidence` record containing the source filename, field name,
extracted value, confidence, extracted text, and user-confirmation state.
Users must confirm document candidates before they are treated as profile
inputs. The supplied payslip is a useful test case because gross earnings,
net pay, and deductions must not be conflated.

Regression coverage is in `backend/tests/test_capacity_and_evidence.py` and
currently covers capacity scoring, conservative guardrails, and payslip field
separation. The next experiment should measure extraction F1, confidence
calibration, contradiction detection, recommendation stability, and user
comprehension against a questionnaire-only baseline.

---

## Also added along the way

- `app.agent.run_agent` now returns `latency_ms` and `total_tokens` per call
  (needed for 2b, also generally useful for monitoring).
- `retrieve_user_context()` takes a `mode` parameter (`"no_memory"` /
  `"full_history"` / `"lexical_rag"`, default `"lexical_rag"`) instead of
  only supporting the lexical-RAG path. The `/api/agent/query` endpoint
  accepts an optional `retrieval_mode` field for the same reason — leave it
  unset in production, it's there for experimentation.
- `backend/tests/` — a small pytest suite for both new modules
  (`python -m pytest tests/ -v` from `backend/`).
