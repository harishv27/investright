from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


def get_current_user_safe(authorization: Optional[str] = Header(default=None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    try:
        email = auth.decode_access_token(token)
        return db.query(models.User).filter(models.User.email == email).first()
    except Exception:
        return None


@router.post("", response_model=schemas.FeedbackResponse)
def submit_feedback(
    payload: schemas.FeedbackCreateRequest,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_safe),
):
    feedback = models.UserFeedback(
        user_id=current_user.id if current_user else None,
        user_email=current_user.email if current_user else "anonymous@user.com",
        user_name=current_user.full_name if current_user and current_user.full_name else (current_user.email if current_user else "Verified User"),
        overall_rating=payload.overall_rating,
        voice_feature_rating=payload.voice_feature_rating,
        text_chat_rating=payload.text_chat_rating,
        ai_advisor_rating=payload.ai_advisor_rating,
        user_friendly_rating=payload.user_friendly_rating,
        document_extraction_rating=payload.document_extraction_rating,
        multilingual_rating=payload.multilingual_rating,
        nps_score=payload.nps_score,
        most_valuable_feature=payload.most_valuable_feature,
        suggestions=payload.suggestions,
        created_at=datetime.utcnow(),
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


@router.get("/summary", response_model=schemas.FeedbackSummaryResponse)
def get_feedback_summary(db: Session = Depends(get_db)):
    feedbacks = db.query(models.UserFeedback).order_by(models.UserFeedback.created_at.desc()).all()
    count = len(feedbacks)
    if count == 0:
        return schemas.FeedbackSummaryResponse(
            total_feedbacks=0,
            average_overall=5.0,
            average_voice=5.0,
            average_chat=5.0,
            average_ai_advisor=5.0,
            average_user_friendly=5.0,
            average_doc_extraction=5.0,
            average_multilingual=5.0,
            average_nps=10.0,
            recent_feedbacks=[],
        )

    def avg(lst):
        return round(sum(lst) / len(lst), 1) if lst else 5.0

    return schemas.FeedbackSummaryResponse(
        total_feedbacks=count,
        average_overall=avg([f.overall_rating for f in feedbacks]),
        average_voice=avg([f.voice_feature_rating for f in feedbacks]),
        average_chat=avg([f.text_chat_rating for f in feedbacks]),
        average_ai_advisor=avg([f.ai_advisor_rating for f in feedbacks]),
        average_user_friendly=avg([f.user_friendly_rating for f in feedbacks]),
        average_doc_extraction=avg([f.document_extraction_rating for f in feedbacks]),
        average_multilingual=avg([f.multilingual_rating for f in feedbacks]),
        average_nps=avg([f.nps_score for f in feedbacks]),
        recent_feedbacks=feedbacks[:10],
    )


@router.get("", response_model=list[schemas.FeedbackResponse])
def list_feedbacks(db: Session = Depends(get_db)):
    return db.query(models.UserFeedback).order_by(models.UserFeedback.created_at.desc()).limit(100).all()
