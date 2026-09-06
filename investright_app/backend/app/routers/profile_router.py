from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth
from app.media_extraction import extract_candidates, extract_media

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.post("/extract-media", response_model=schemas.MediaExtractionResponse)
async def extract_profile_media(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    allowed_types = {"application/pdf", "image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=415, detail="Upload a PDF, JPG, PNG, or WEBP file")
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File must be 10 MB or smaller")
    try:
        text = extract_media(content, file.content_type)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not extract text from this file: {exc}") from exc
    candidates = extract_candidates(text)
    evidence_ids = {}
    for field_name, value in candidates.items():
        if value is None:
            continue
        confidence = 0.82 if field_name in {"net_pay", "gross_earnings"} else 0.62
        evidence = models.FinancialEvidence(
            user_id=current_user.id,
            filename=file.filename or "uploaded-document",
            source_type="uploaded_document",
            field_name=field_name,
            extracted_value=value,
            confidence=confidence,
            extracted_text=text[:5000],
        )
        db.add(evidence)
        db.flush()
        evidence_ids[field_name] = evidence.id
    db.commit()
    return {
        "filename": file.filename or "uploaded-document",
        "media_type": file.content_type,
        "extracted_text": text[:5000],
        "candidates": candidates,
        "confidence_note": "These are OCR/text candidates only. Review every value before continuing.",
        "evidence_ids": evidence_ids,
    }


@router.get("/evidence", response_model=list[schemas.EvidenceResponse])
def get_evidence(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return (
        db.query(models.FinancialEvidence)
        .filter(models.FinancialEvidence.user_id == current_user.id)
        .order_by(models.FinancialEvidence.created_at.desc())
        .limit(100)
        .all()
    )


@router.post("/evidence/{evidence_id}/confirm", response_model=schemas.EvidenceResponse)
def confirm_evidence(
    evidence_id: int,
    payload: schemas.EvidenceConfirmationRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    evidence = db.query(models.FinancialEvidence).filter(
        models.FinancialEvidence.id == evidence_id,
        models.FinancialEvidence.user_id == current_user.id,
    ).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence record not found")
    evidence.confirmed_value = payload.value
    evidence.confirmed = 1
    evidence.confirmed_at = datetime.utcnow()
    db.commit()
    db.refresh(evidence)
    return evidence


@router.post("", response_model=schemas.ProfileResponse)
def upsert_profile(
    payload: schemas.ProfileRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    profile = db.query(models.FinancialProfile).filter(
        models.FinancialProfile.user_id == current_user.id
    ).first()

    if profile:
        for field, value in payload.model_dump().items():
            setattr(profile, field, value)
    else:
        profile = models.FinancialProfile(user_id=current_user.id, **payload.model_dump())
        db.add(profile)

    db.commit()
    db.refresh(profile)
    return profile


@router.get("", response_model=schemas.ProfileResponse)
def get_profile(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    profile = db.query(models.FinancialProfile).filter(
        models.FinancialProfile.user_id == current_user.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="No financial profile found yet")
    return profile
