# InvestRight

InvestRight is a responsive web application for evidence-backed financial risk profiling and personalized investment decision support. It combines deterministic financial calculations with a retrieval-grounded AI advisor. Recommendations expose their evidence and do not treat unverified OCR output or old conversation text as current financial truth.

This repository contains the implementation and research artifacts for *AI-Assisted Financial Risk Profiling and Personalized Investment Decision Support*.

## What makes this version different

InvestRight separates three concepts:

- **Risk willingness**: how comfortable a user is with investment volatility.
- **Financial capacity**: whether income, expenses, savings, and planned contributions show that the user can absorb volatility.
- **Evidence quality**: whether a value came from a document, when it was extracted, how confident extraction was, and whether the user confirmed it.

When willingness is higher than capacity, the recommendation applies a conservative guardrail and explains why. Uploaded payslips and statements become reviewable evidence records instead of disappearing after an OCR request.

## Product capabilities

- Responsive desktop web workspace with sidebar navigation and mobile fallback
- Email/password authentication and optional Google authentication
- Conversational financial-profile onboarding
- Risk-willingness assessment
- Deterministic savings, expense, contribution, and capacity calculations
- PDF, JPG, PNG, and WEBP document extraction
- Payslip-aware extraction for net pay, gross earnings, deductions, income, and savings candidates
- Evidence ledger with extraction confidence and user confirmation state
- Capacity score, emergency-fund coverage, and recommendation guardrails
- Portfolio holdings and return tracking
- Goal planner with SIP illustrations
- AI advisor with tool calling, Indian-rupee formatting, and source metadata
- Provenance-aware lexical RAG over current profile facts and prior exchanges
- Offline retrieval evaluation and calibrated risk-band experiments

The AI advisor is decision support, not licensed financial advice. Investment performance is not guaranteed. Users should verify current fund, fee, tax, and platform information independently.

## Repository structure

```text
investright/
├── backend/
│   ├── app/
│   │   ├── main.py                 FastAPI application and route registration
│   │   ├── config.py               Environment-backed settings
│   │   ├── database.py             SQLAlchemy engine and schema bootstrap
│   │   ├── models.py               Users, profiles, evidence, risk, portfolio
│   │   ├── schemas.py              Pydantic API contracts
│   │   ├── auth.py                 Password hashing and JWT authentication
│   │   ├── analytics.py            Deterministic financial calculations
│   │   ├── capacity.py             Capacity scoring and risk guardrails
│   │   ├── media_extraction.py     PDF/OCR extraction and candidate parsing
│   │   ├── risk.py                 Risk willingness scoring
│   │   ├── risk_calibration.py     Reference-population calibration
│   │   ├── recommendation.py       Risk/horizon category matching
│   │   ├── retrieval.py            Provenance-aware context retrieval
│   │   ├── retrieval_eval.py       Offline retrieval experiments
│   │   ├── agent.py                Groq tool-calling advisor
│   │   └── routers/                Auth, profile, risk, dashboard, agent, portfolio
│   ├── scripts/                    Calibration and retrieval experiments
│   ├── tests/                      Backend regression tests
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx                 Responsive web shell and navigation
│   │   ├── App.css                 Web workspace styling
│   │   ├── api/client.js            Backend API wrapper
│   │   └── screens/                 Auth, onboarding, chat, dashboard, profile
│   ├── package.json
│   └── .env.example
├── documents/                      Literature exports and project documents
├── RESULTS.md                      Retrieval and risk-calibration results
└── README.md
```

## Requirements

- Python 3.10-3.13
- Node.js 18 or newer
- Tesseract OCR for image uploads (`brew install tesseract` on macOS)
- Optional Groq API key for live AI advisor responses

The application works without a Groq key. Deterministic profile, risk, capacity, evidence, dashboard, portfolio, and goal-planning features do not require an LLM.

## Run locally

### Backend

```bash
cd backend
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env` before a shared or public deployment:

```dotenv
DATABASE_URL=sqlite:///./investright.db
JWT_SECRET=replace-with-a-long-random-secret
CORS_ORIGINS=http://localhost:5173
GROQ_API_KEY=
```

Start the API:

```bash
uvicorn app.main:app --reload --port 8000
```

The API is available at http://localhost:8000 and Swagger documentation is available at http://localhost:8000/docs.

For PostgreSQL, install `psycopg2-binary` and set `DATABASE_URL` to a PostgreSQL connection string. The current development bootstrap creates tables automatically; production should use Alembic migrations.

### Frontend

In a second terminal:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open http://localhost:5173. Set `VITE_API_URL` to the deployed backend HTTPS origin before a production build.

## Main API routes

All routes except authentication and health checks require a bearer token.

| Route | Purpose |
| --- | --- |
| `POST /api/auth/signup` | Create an account |
| `POST /api/auth/login` | Create a session |
| `GET /api/auth/me` | Read the current user |
| `POST /api/profile` | Create or update the financial profile |
| `POST /api/profile/extract-media` | Extract document candidates and persist evidence |
| `GET /api/profile/evidence` | List the user's evidence records |
| `POST /api/profile/evidence/{id}/confirm` | Confirm an extracted value |
| `POST /api/risk-assessment` | Store a risk-willingness assessment |
| `GET /api/dashboard` | Return analytics, capacity, guardrails, and recommendations |
| `GET/POST/DELETE /api/portfolio` | Manage portfolio holdings |
| `GET /api/agent/conversations` | Read prior advisor conversations |
| `POST /api/agent/query` | Ask the retrieval-grounded AI advisor |
| `GET /api/health` | Health check |

## Evidence workflow

1. Upload a payslip or statement in **Ask Fin**.
2. The backend extracts text and candidate financial fields.
3. Each numeric candidate is saved with source filename, extraction confidence, and timestamp.
4. The user reviews the candidates and confirms the values to use.
5. Confirmed values are visible in **Profile -> Evidence ledger** and the confirmed count is shown on the dashboard.

OCR candidates are never treated as authoritative automatically. The sample payslip in `documents/` demonstrates why this matters: gross earnings, net pay, and deductions are different financial concepts.

## Capacity and recommendation logic

The capacity engine uses deterministic calculations:

- Emergency-fund coverage in months
- Monthly surplus
- Expense ratio
- Planned-contribution ratio

These produce a 0-100 capacity score and one of `Limited`, `Resilient`, or `Strong`. The final investment decision category is derived from willingness and capacity:

- Limited capacity caps non-conservative willingness at Conservative.
- Resilient capacity caps Aggressive willingness at Moderate.
- Strong capacity preserves the stated willingness category.

The dashboard shows both the original willingness result and the final guarded decision so the adjustment is inspectable rather than hidden.

## Testing and validation

Backend tests use the repository virtual environment:

```bash
cd backend
./venv/bin/python -m pytest tests/ -q
./venv/bin/python -m compileall -q app
```

Frontend checks:

```bash
cd frontend
npm run lint
npm run build
```

The test suite covers risk calibration, retrieval ranking, capacity scoring, capacity guardrails, and payslip field extraction.

## Research artifacts

The project includes a reproducible retrieval comparison in [RESULTS.md](RESULTS.md):

- `no_memory`
- `full_history`
- `lexical_rag`

The offline experiment measures precision@k, context size, assembly latency, and stale-item exposure. The current result shows lexical retrieval reaching 0.99 precision@4 with substantially smaller context than full history.

Risk thresholds are calibrated from a reference population and can later be recalibrated from anonymized response sets:

```bash
cd backend
python -m scripts.calibrate_risk_thresholds
```

The next publication-grade experiment is longitudinal evaluation of risk drift: compare static questionnaire-only recommendations against the capacity-aware system after income, expenses, savings, or evidence freshness changes.

## Production checklist

- Replace `Base.metadata.create_all` with Alembic migrations.
- Use PostgreSQL or another managed database instead of local SQLite.
- Set a strong `JWT_SECRET` and HTTPS-only CORS origins.
- Add rate limiting and request-cost monitoring to `/api/agent/query`.
- Add malware scanning and encrypted storage if original documents are retained.
- Replace the illustrative platform catalog with verified, maintained data.
- Add human review and consent procedures before collecting real financial documents for research.
- Run the LLM-dependent RAG experiment with a real `GROQ_API_KEY`.
- Validate risk-band thresholds with anonymized real responses and financial-advisory expertise before making regulated recommendations.
