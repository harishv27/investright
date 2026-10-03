# InvestRight

**Evidence-backed financial risk profiling and personalized investment decision support.**

InvestRight is a full-stack web application that combines deterministic financial calculations with a retrieval-grounded AI advisor. It separates what a user *says* they can tolerate from what their finances can actually *absorb*, and it shows the evidence behind every recommendation.

This repository holds the application and the research artifacts for the paper *AI-Assisted Financial Risk Profiling and Personalized Investment Decision Support*.

> **Disclaimer:** InvestRight is decision support, not licensed financial advice. Investment performance is not guaranteed. Verify fund, fee, tax, and platform information independently.

---

## Table of contents

- [Key ideas](#key-ideas)
- [Features](#features)
- [Tech stack](#tech-stack)
- [Repository layout](#repository-layout)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [API overview](#api-overview)
- [How the recommendation works](#how-the-recommendation-works)
- [Testing](#testing)
- [Research artifacts](#research-artifacts)
- [Production checklist](#production-checklist)

---

## Key ideas

InvestRight keeps three concepts apart:

| Concept | Question it answers |
| --- | --- |
| **Risk willingness** | How comfortable is the user with volatility? |
| **Financial capacity** | Do income, expenses, savings and planned contributions let them absorb it? |
| **Evidence quality** | Where did each value come from, how confident was the extraction, and has the user confirmed it? |

When willingness exceeds capacity, a conservative guardrail applies and the dashboard explains why. OCR output from uploaded payslips or statements is stored as reviewable evidence, never silently trusted.

## Features

- Responsive web workspace (desktop sidebar, mobile fallback)
- Email/password and optional Google sign-in
- Conversational profile onboarding and risk-willingness assessment
- Deterministic savings, expense, contribution and capacity calculations
- PDF / JPG / PNG / WEBP document extraction with payslip-aware parsing
- Evidence ledger with confidence scores and user confirmation
- Capacity score, emergency-fund coverage and recommendation guardrails
- Portfolio holdings, return tracking and a goal planner with SIP illustrations
- AI advisor ("Ask Fin") with tool calling, INR formatting and source metadata
- Provenance-aware lexical RAG over current profile facts and past conversations
- In-app feedback survey and an admin-only evaluation view (benchmarks, LaTeX/CSV exports)
- Offline retrieval evaluation and calibrated risk-band experiments

The core features work **without** an LLM key. Only live advisor responses need `GROQ_API_KEY`.

## Tech stack

| Layer | Technology |
| --- | --- |
| Backend | Python, FastAPI, SQLAlchemy 2, Pydantic 2 |
| Auth | JWT (python-jose), bcrypt, Google ID tokens |
| Database | SQLite by default, PostgreSQL supported |
| Document extraction | pypdf, Pillow, Tesseract OCR |
| AI advisor | Groq (tool-calling LLM), lexical retrieval |
| Frontend | React 19, Vite, oxlint |
| Tests | pytest, httpx |

## Repository layout

```text
investright/
├── investright_app/
│   ├── backend/
│   │   ├── app/                 FastAPI app: models, risk, capacity, retrieval, agent, routers/
│   │   ├── scripts/             Calibration, retrieval and evaluation experiments
│   │   ├── tests/               Backend regression tests
│   │   ├── requirements.txt
│   │   └── .env.example
│   ├── frontend/
│   │   ├── src/                 App shell, API client, screens/
│   │   ├── package.json
│   │   └── .env.example
│   ├── documents/               Sample payslip/image and literature exports
│   ├── README.md                Detailed application documentation
│   └── RESULTS.md               Retrieval and risk-calibration results
├── results_package/             Paper-ready figures, tables, raw data, scripts
│   ├── RESEARCH_RESULTS.md      Start here for the research write-up
│   └── figures/  tables/  raw_data/
└── README.md
```

## Quick start

**Prerequisites:** Python 3.10–3.13, Node.js 18+, and Tesseract OCR for image uploads (`brew install tesseract` on macOS). A Groq API key is optional.

### 1. Backend

```bash
cd investright_app/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then set JWT_SECRET
uvicorn app.main:app --reload --port 8000
```

API: <http://localhost:8000> · Swagger docs: <http://localhost:8000/docs>

### 2. Frontend

In a second terminal:

```bash
cd investright_app/frontend
npm install
cp .env.example .env
npm run dev
```

Open <http://localhost:5173>.

## Configuration

**Backend** (`investright_app/backend/.env`)

| Variable | Purpose | Default |
| --- | --- | --- |
| `DATABASE_URL` | SQLAlchemy URL | `sqlite:///./investright.db` |
| `JWT_SECRET` | Token signing secret. **Change it.** | placeholder |
| `JWT_ALGORITHM` / `JWT_EXPIRE_MINUTES` | Token settings | `HS256` / `10080` |
| `GOOGLE_CLIENT_ID` | Enables Google sign-in | empty |
| `GROQ_API_KEY` | Enables live AI advisor | empty |
| `GROQ_MODEL` | Groq tool-calling model | `llama-3.3-70b-versatile` |
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:5173` |

**Frontend** (`investright_app/frontend/.env`)

| Variable | Purpose |
| --- | --- |
| `VITE_API_URL` | Backend origin (use HTTPS in production) |
| `VITE_GOOGLE_CLIENT_ID` | Google OAuth web client ID |

Never commit `.env` files; they are git-ignored.

## API overview

All routes except `/api/auth/*` and `/api/health` require a bearer token.

| Area | Routes |
| --- | --- |
| Auth | `POST /api/auth/signup`, `/login`, `/google` · `GET /api/auth/me` |
| Profile | `GET/POST /api/profile` · `POST /api/profile/extract-media` |
| Evidence | `GET /api/profile/evidence` · `POST /api/profile/evidence/{id}/confirm` |
| Risk | `POST /api/risk-assessment` · `GET /api/risk-assessment/latest` |
| Dashboard | `GET /api/dashboard` |
| Portfolio | `GET/POST /api/portfolio` · `DELETE /api/portfolio/{id}` |
| Advisor | `GET /api/agent/conversations` · `POST /api/agent/query` |
| Feedback | `POST/GET /api/feedback` · `GET /api/feedback/summary` |
| Evaluation (admin) | `GET /api/evaluation/benchmark-5-users`, `/paper-latex`, `/export-zip` · `POST /api/evaluation/re-evaluate` |
| Health | `GET /api/health` |

## How the recommendation works

1. **Willingness** is scored from the risk questionnaire.
2. **Capacity** is a 0–100 score from emergency-fund months, monthly surplus, expense ratio and planned-contribution ratio, labelled `Limited`, `Resilient` or `Strong`.
3. **Guardrail** combines them:
   - `Limited` caps any non-conservative willingness at *Conservative*.
   - `Resilient` caps *Aggressive* at *Moderate*.
   - `Strong` keeps the stated willingness.
4. The dashboard shows both the original and the guarded result, so the adjustment is visible.

**Evidence workflow:** upload a document in Ask Fin → candidate values are extracted and saved with filename, confidence and timestamp → the user reviews and confirms → confirmed values appear in *Profile → Evidence ledger*.

## Testing

```bash
# Backend
cd investright_app/backend
python -m pytest tests/ -q

# Frontend
cd investright_app/frontend
npm run lint
npm run build
```

Tests cover risk calibration, retrieval ranking, capacity scoring and guardrails, profile sync, feedback and evaluation endpoints, and payslip field extraction.

## Research artifacts

- [`results_package/RESEARCH_RESULTS.md`](results_package/RESEARCH_RESULTS.md) is the main report: Table IV/V reproduction, risk-distribution figures, retrieval experiment, calibration parameters and suggested next steps.
- [`investright_app/RESULTS.md`](investright_app/RESULTS.md) holds the retrieval comparison (`no_memory`, `full_history`, `lexical_rag`).
- Everything is reproducible: scripts in `investright_app/backend/scripts/` run against the real backend code and need no API key or network.

```bash
cd investright_app/backend
python -m scripts.calibrate_risk_thresholds
```

## Production checklist

- Replace `Base.metadata.create_all` with Alembic migrations.
- Use PostgreSQL (or another managed database) instead of local SQLite.
- Set a strong `JWT_SECRET` and HTTPS-only CORS origins.
- Rate-limit and monitor cost on `/api/agent/query`.
- Add malware scanning and encrypted storage if original documents are kept.
- Replace the illustrative platform catalog with verified, maintained data.
- Obtain consent and human review before collecting real financial documents.
- Validate risk-band thresholds with real, anonymized responses and advisory expertise before any regulated use.
