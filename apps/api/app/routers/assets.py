from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Asset
from app.db.session import get_session
from app.schemas import AssetCreate, AssetRead
from app.dependencies.rate_limit import enforce_rate_limit
from app.utils.assets import get_or_create_asset

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
    asset = get_or_create_asset(
        session,
        payload.ticker,
        asset_type_hint=payload.type,
        name=payload.name,
        exchange=payload.exchange,
    )
    session.flush()
    session.refresh(asset)
    return asset
