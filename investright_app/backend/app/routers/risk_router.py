from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth
from app.risk import score_risk

router = APIRouter(prefix="/api/risk-assessment", tags=["risk"])


@router.post("", response_model=schemas.RiskAssessmentResponse)
def submit_risk_assessment(
    payload: schemas.RiskAssessmentRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    result = score_risk(payload.responses)

    record = models.RiskAssessment(
        user_id=current_user.id,
        responses=payload.responses,
        score=result["score"],
        risk_category=result["risk_category"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/latest", response_model=schemas.RiskAssessmentResponse)
def get_latest_risk_assessment(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    record = (
        db.query(models.RiskAssessment)
        .filter(models.RiskAssessment.user_id == current_user.id)
        .order_by(models.RiskAssessment.created_at.desc())
        .first()
    )
    if not record:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="No risk assessment found yet")
    return record
