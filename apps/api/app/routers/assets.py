from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Asset
from app.db.session import get_session
from app.schemas import AssetCreate, AssetRead

router = APIRouter()


@router.get("/", response_model=Sequence[AssetRead])
def list_assets(session: Session = Depends(get_session)) -> Sequence[Asset]:
    stmt = select(Asset).order_by(Asset.ticker.asc())
    return session.scalars(stmt).all()


@router.post("/", response_model=AssetRead, status_code=status.HTTP_201_CREATED)
def create_asset(
    payload: AssetCreate,
    session: Session = Depends(get_session),
) -> Asset:
    exists_stmt = select(Asset).where(
        Asset.ticker == payload.ticker, Asset.type == payload.type
    )
    existing = session.scalars(exists_stmt).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Asset {payload.ticker} ({payload.type}) already exists",
        )

    asset = Asset(
        ticker=payload.ticker.upper(),
        name=payload.name,
        type=payload.type,
        exchange=payload.exchange,
    )
    session.add(asset)
    session.flush()
    session.refresh(asset)
    return asset
