from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import ensure_schema
from app.config import settings
from app.routers import auth_router, profile_router, risk_router, dashboard_router, agent_router, portfolio_router, feedback_router, evaluation_router

# Creates tables on startup if they don't exist yet.
# For production, switch to Alembic migrations instead.
ensure_schema()

app = FastAPI(
    title="InvestRight API",
    description="AI-assisted financial risk profiling and investment decision support.",
    version="1.0.0",
)

cors_origins = list(set(settings.cors_origin_list + [
    "https://investright-tawny.vercel.app",
    "http://localhost:5173",
    "http://localhost:3000",
]))

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app|http://localhost:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(profile_router.router)
app.include_router(risk_router.router)
app.include_router(dashboard_router.router)
app.include_router(agent_router.router)
app.include_router(portfolio_router.router)
app.include_router(feedback_router.router)
app.include_router(evaluation_router.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
