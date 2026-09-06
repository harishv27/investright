from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ---------- Auth ----------

class SignupRequest(BaseModel):
    email: EmailStr
    full_name: Optional[str] = Field(default=None, max_length=100)
    password: str = Field(min_length=6)
    age: Optional[int] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleLoginRequest(BaseModel):
    credential: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    full_name: Optional[str] = None
    email: EmailStr
    age: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=100)


class PortfolioHoldingRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    asset_type: str = Field(min_length=1, max_length=40)
    invested_amount: float = Field(gt=0)
    current_value: float = Field(ge=0)


class PortfolioHoldingResponse(PortfolioHoldingRequest):
    id: int
    return_amount: float
    return_pct: float

    class Config:
        from_attributes = True


class PortfolioResponse(BaseModel):
    total_invested: float
    current_value: float
    return_amount: float
    return_pct: float
    holdings: list[PortfolioHoldingResponse]


# ---------- Financial profile ----------

class ProfileRequest(BaseModel):
    income: float = Field(gt=0)
    expenses: float = Field(ge=0)
    savings: float = Field(ge=0)
    planned_investment: float = Field(ge=0)
    goal: str
    horizon_years: int = Field(ge=0, le=60)


class ProfileResponse(ProfileRequest):
    id: int

    class Config:
        from_attributes = True


class MediaExtractionResponse(BaseModel):
    filename: str
    media_type: str
    extracted_text: str
    candidates: dict[str, Optional[float]]
    confidence_note: str
    evidence_ids: dict[str, int] = {}


class EvidenceResponse(BaseModel):
    id: int
    filename: str
    source_type: str
    field_name: str
    extracted_value: float
    confirmed_value: Optional[float] = None
    confidence: float
    confirmed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class EvidenceConfirmationRequest(BaseModel):
    value: float = Field(ge=0)


# ---------- Risk assessment ----------

class RiskAssessmentRequest(BaseModel):
    responses: list[int] = Field(min_length=1)


class RiskAssessmentResponse(BaseModel):
    id: int
    score: int
    risk_category: str

    class Config:
        from_attributes = True


# ---------- Dashboard ----------

class DashboardResponse(BaseModel):
    monthly_savings: float
    savings_rate_pct: float
    expense_ratio_pct: float
    investment_capacity: float
    risk_score: Optional[int] = None
    risk_category: Optional[str] = None
    recommended_category: Optional[str] = None
    recommendation_rationale: Optional[str] = None
    recommendation_history: list[dict] = []
    capacity_score: Optional[float] = None
    capacity_category: Optional[str] = None
    emergency_months: Optional[float] = None
    capacity_guidance: Optional[str] = None
    evidence_count: int = 0
    decision_risk_category: Optional[str] = None
    decision_risk_explanation: Optional[str] = None


# ---------- Agent ----------

class AgentQueryRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    retrieval_mode: Optional[str] = Field(
        default="lexical_rag",
        description="One of 'no_memory', 'full_history', 'lexical_rag'. "
                    "Exposed mainly for the RAG comparison experiment; "
                    "production clients should leave this at the default.",
    )


class AgentQueryResponse(BaseModel):
    answer: str
    tool_trace: list[dict]
    retrieval_sources: list[dict] = []
    latency_ms: float = 0.0
    total_tokens: int = 0


class ConversationResponse(BaseModel):
    id: int
    query: str
    response: str
    created_at: datetime

    class Config:
        from_attributes = True
