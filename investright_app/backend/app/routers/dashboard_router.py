from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth
from app.analytics import calculate_financials
from app.capacity import adjust_risk_for_capacity, calculate_capacity
from app.recommendation import match_investment_category

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=schemas.DashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    profile = db.query(models.FinancialProfile).filter(
        models.FinancialProfile.user_id == current_user.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Complete your financial profile first")

    financials = calculate_financials(profile.income, profile.expenses, profile.planned_investment)
    capacity = calculate_capacity(
        profile.income, profile.expenses, profile.savings, profile.planned_investment,
    )

    latest_risk = (
        db.query(models.RiskAssessment)
        .filter(models.RiskAssessment.user_id == current_user.id)
        .order_by(models.RiskAssessment.created_at.desc())
        .first()
    )

    response = schemas.DashboardResponse(
        **financials,
        capacity_score=capacity["capacity_score"],
        capacity_category=capacity["capacity_category"],
        emergency_months=capacity["emergency_months"],
        capacity_guidance=capacity["guidance"],
        evidence_count=db.query(models.FinancialEvidence).filter(
            models.FinancialEvidence.user_id == current_user.id,
            models.FinancialEvidence.confirmed == 1,
        ).count(),
    )

    if latest_risk:
        response.risk_score = latest_risk.score
        response.risk_category = latest_risk.risk_category

        decision_category, decision_explanation = adjust_risk_for_capacity(
            latest_risk.risk_category, capacity["capacity_category"],
        )
        response.decision_risk_category = decision_category
        response.decision_risk_explanation = decision_explanation
        match = match_investment_category(decision_category, profile.horizon_years)
        response.recommended_category = match["recommended_category"]
        response.recommendation_rationale = match["rationale"]

        latest_recommendation = (
            db.query(models.Recommendation)
            .filter(models.Recommendation.user_id == current_user.id)
            .order_by(models.Recommendation.created_at.desc())
            .first()
        )
        if not latest_recommendation or (
            latest_recommendation.category != match["recommended_category"]
            or latest_recommendation.rationale != match["rationale"]
        ):
            rec = models.Recommendation(
                user_id=current_user.id,
                category=match["recommended_category"],
                rationale=match["rationale"],
            )
            db.add(rec)
            db.commit()

    history = (
        db.query(models.Recommendation)
        .filter(models.Recommendation.user_id == current_user.id)
        .order_by(models.Recommendation.created_at.desc())
        .limit(10)
        .all()
    )
    response.recommendation_history = [
        {"category": item.category, "rationale": item.rationale, "created_at": item.created_at.isoformat()}
        for item in history
    ]

    return response
