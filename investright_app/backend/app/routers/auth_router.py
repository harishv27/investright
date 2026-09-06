from fastapi import APIRouter, Depends, HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from secrets import token_urlsafe
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/me", response_model=schemas.UserResponse)
def get_current_user_details(
    current_user: models.User = Depends(auth.get_current_user),
):
    return current_user


@router.patch("/me", response_model=schemas.UserResponse)
def update_current_user_details(
    payload: schemas.UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    current_user.full_name = payload.full_name.strip()
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/signup", response_model=schemas.TokenResponse)
def signup(payload: schemas.SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    user = models.User(
        email=payload.email,
        full_name=payload.full_name.strip() if payload.full_name else None,
        hashed_password=auth.hash_password(payload.password),
        age=payload.age,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = auth.create_access_token(subject=user.email)
    return schemas.TokenResponse(access_token=token)


@router.post("/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not auth.verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    token = auth.create_access_token(subject=user.email)
    return schemas.TokenResponse(access_token=token)


@router.post("/google", response_model=schemas.TokenResponse)
def google_login(payload: schemas.GoogleLoginRequest, db: Session = Depends(get_db)):
    if not settings.google_client_id:
        raise HTTPException(status_code=503, detail="Google login is not configured")

    try:
        claims = id_token.verify_oauth2_token(
            payload.credential,
            google_requests.Request(),
            settings.google_client_id,
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google credential")

    email = claims.get("email")
    if not email or not claims.get("email_verified"):
        raise HTTPException(status_code=401, detail="Google account email is not verified")

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        user = models.User(
            email=email,
            full_name=claims.get("name") or claims.get("given_name"),
            hashed_password=auth.hash_password(token_urlsafe(32)),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = auth.create_access_token(subject=user.email)
    return schemas.TokenResponse(access_token=token)
