from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Asset
from app.db.session import get_session
from app.schemas import AssetCreate, AssetRead
from app.dependencies.rate_limit import enforce_rate_limit
from app.utils.tickers import resolve_ticker

router = APIRouter()


@router.get("/", response_model=Sequence[AssetRead])
def list_assets(
    session: Session = Depends(get_session),
    _: None = Depends(enforce_rate_limit),
) -> Sequence[Asset]:
    stmt = select(Asset).order_by(Asset.ticker.asc())
    return session.scalars(stmt).all()


@router.post("/", response_model=AssetRead, status_code=status.HTTP_201_CREATED)
def create_asset(
    payload: AssetCreate,
    session: Session = Depends(get_session),
    _: None = Depends(enforce_rate_limit),
) -> Asset:
    canonical, display = resolve_ticker(payload.ticker)

    exists_stmt = select(Asset).where(Asset.ticker == canonical, Asset.type == payload.type)
    existing = session.scalars(exists_stmt).first()
    if existing:
        if display and existing.display_ticker != display:
            existing.display_ticker = display
            session.add(existing)
            session.flush()
            session.refresh(existing)
        return existing

    asset = Asset(
        ticker=canonical,
        display_ticker=display,
        name=payload.name,
        type=payload.type,
        exchange=payload.exchange,
    )
    session.add(asset)
    session.flush()
    session.refresh(asset)
    return asset
