from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import auth, models, schemas

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


def holding_response(holding: models.PortfolioHolding) -> schemas.PortfolioHoldingResponse:
    return schemas.PortfolioHoldingResponse(
        id=holding.id,
        name=holding.name,
        asset_type=holding.asset_type,
        invested_amount=holding.invested_amount,
        current_value=holding.current_value,
        return_amount=holding.current_value - holding.invested_amount,
        return_pct=round((holding.current_value / holding.invested_amount - 1) * 100, 2),
    )


@router.get("", response_model=schemas.PortfolioResponse)
def get_portfolio(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    holdings = db.query(models.PortfolioHolding).filter(
        models.PortfolioHolding.user_id == current_user.id
    ).order_by(models.PortfolioHolding.updated_at.desc()).all()
    total_invested = sum(holding.invested_amount for holding in holdings)
    current_value = sum(holding.current_value for holding in holdings)
    return schemas.PortfolioResponse(
        total_invested=total_invested,
        current_value=current_value,
        return_amount=current_value - total_invested,
        return_pct=round((current_value / total_invested - 1) * 100, 2) if total_invested else 0,
        holdings=[holding_response(holding) for holding in holdings],
    )


@router.post("", response_model=schemas.PortfolioHoldingResponse, status_code=201)
def add_holding(
    payload: schemas.PortfolioHoldingRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    holding = models.PortfolioHolding(user_id=current_user.id, **payload.model_dump())
    db.add(holding)
    db.commit()
    db.refresh(holding)
    return holding_response(holding)


@router.delete("/{holding_id}", status_code=204)
def delete_holding(
    holding_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    holding = db.query(models.PortfolioHolding).filter(
        models.PortfolioHolding.id == holding_id,
        models.PortfolioHolding.user_id == current_user.id,
    ).first()
    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found")
    db.delete(holding)
    db.commit()