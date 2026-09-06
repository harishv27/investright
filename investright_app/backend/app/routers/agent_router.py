from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth
from app.agent import run_agent
from app.retrieval import retrieve_user_context

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.get("/conversations", response_model=list[schemas.ConversationResponse])
def get_conversations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return (
        db.query(models.Conversation)
        .filter(models.Conversation.user_id == current_user.id)
        .order_by(models.Conversation.created_at.asc())
        .limit(50)
        .all()
    )


@router.post("/query", response_model=schemas.AgentQueryResponse)
def agent_query(
    payload: schemas.AgentQueryRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    profile = db.query(models.FinancialProfile).filter(
        models.FinancialProfile.user_id == current_user.id
    ).first()
    latest_risk = (
        db.query(models.RiskAssessment)
        .filter(models.RiskAssessment.user_id == current_user.id)
        .order_by(models.RiskAssessment.created_at.desc())
        .first()
    )

    latest_recommendation = (
        db.query(models.Recommendation)
        .filter(models.Recommendation.user_id == current_user.id)
        .order_by(models.Recommendation.created_at.desc())
        .first()
    )

    context, retrieval_sources = retrieve_user_context(
        db, current_user.id, payload.message, profile, latest_risk, latest_recommendation,
        mode=payload.retrieval_mode or "lexical_rag",
    )
    context["user_identity"] = {
        "full_name": current_user.full_name,
        "email": current_user.email,
        "age": current_user.age,
    }

    recent_convs = (
        db.query(models.Conversation)
        .filter(models.Conversation.user_id == current_user.id)
        .order_by(models.Conversation.created_at.desc())
        .limit(6)
        .all()
    )
    recent_convs.reverse()

    conversation_history = []
    for c in recent_convs:
        conversation_history.append({"role": "user", "content": c.query})
        conversation_history.append({"role": "assistant", "content": c.response})

    result = run_agent(payload.message, context, conversation_history=conversation_history, retrieval_sources=retrieval_sources)

    conversation = models.Conversation(
        user_id=current_user.id,
        query=payload.message,
        response=result["answer"],
        tool_trace=result["tool_trace"],
    )
    db.add(conversation)
    db.commit()

    return result
