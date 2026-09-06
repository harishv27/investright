from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    age = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("FinancialProfile", back_populates="user", uselist=False)
    risk_assessments = relationship("RiskAssessment", back_populates="user")
    recommendations = relationship("Recommendation", back_populates="user")
    portfolio_holdings = relationship("PortfolioHolding", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")

    @property
    def is_admin(self) -> bool:
        return (self.email or "").lower() in ("admin", "admin@investright.com", "admin@gmail.com")


class FinancialProfile(Base):
    __tablename__ = "financial_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    income = Column(Float, nullable=False)
    expenses = Column(Float, nullable=False)
    savings = Column(Float, nullable=False)
    planned_investment = Column(Float, nullable=False)
    goal = Column(String, nullable=False)
    horizon_years = Column(Integer, nullable=False)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    responses = Column(JSON, nullable=False)  # list[int]
    score = Column(Integer, nullable=False)
    risk_category = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="risk_assessments")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    category = Column(String, nullable=False)
    rationale = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="recommendations")


class PortfolioHolding(Base):
    __tablename__ = "portfolio_holdings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    asset_type = Column(String, nullable=False)
    invested_amount = Column(Float, nullable=False)
    current_value = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="portfolio_holdings")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    tool_trace = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="conversations")


class FinancialEvidence(Base):
    __tablename__ = "financial_evidence"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    field_name = Column(String, nullable=False)
    extracted_value = Column(Float, nullable=False)
    confirmed_value = Column(Float, nullable=True)
    confidence = Column(Float, nullable=False, default=0.0)
    source_page = Column(Integer, nullable=True)
    extracted_text = Column(Text, nullable=True)
    confirmed = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)

    user = relationship("User")


class UserFeedback(Base):
    __tablename__ = "user_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_email = Column(String, nullable=True)
    user_name = Column(String, nullable=True)

    # Core rating questions (1-5 scale)
    overall_rating = Column(Integer, nullable=False, default=5)
    voice_feature_rating = Column(Integer, nullable=False, default=5)
    text_chat_rating = Column(Integer, nullable=False, default=5)
    ai_advisor_rating = Column(Integer, nullable=False, default=5)
    user_friendly_rating = Column(Integer, nullable=False, default=5)
    document_extraction_rating = Column(Integer, nullable=False, default=5)
    multilingual_rating = Column(Integer, nullable=False, default=5)

    # NPS score (1-10)
    nps_score = Column(Integer, nullable=False, default=10)

    # Qualitative feedback
    most_valuable_feature = Column(String, nullable=True)
    suggestions = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
