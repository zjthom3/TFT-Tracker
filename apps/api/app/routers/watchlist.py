from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.models import Asset, UserAsset
from app.db.session import get_session
from app.dependencies.auth import get_current_user
from app.schemas import WatchlistAdd, WatchlistItem, WatchlistOrder
from app.utils.assets import get_or_create_asset
from app.utils.tickers import resolve_ticker

router = APIRouter()


def _to_watchlist_item(user_asset: UserAsset, asset: Asset) -> WatchlistItem:
    return WatchlistItem(
        ticker=asset.ticker,
        display_ticker=asset.display_ticker or asset.ticker,
        name=asset.name,
        type=asset.type,
        order=user_asset.display_order,
    )


@router.get("/watchlist", response_model=list[WatchlistItem])
def list_watchlist(
    user=Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[WatchlistItem]:
    rows = (
        session.execute(
            select(UserAsset, Asset)
            .join(Asset, UserAsset.asset_id == Asset.id)
            .where(UserAsset.user_id == user.id)
            .order_by(UserAsset.display_order.asc().nullslast(), UserAsset.created_at.asc())
        )
        .all()
    )
    return [_to_watchlist_item(user_asset, asset) for user_asset, asset in rows]


@router.post("/watchlist", response_model=WatchlistItem, status_code=status.HTTP_201_CREATED)
def add_watchlist_item(
    payload: WatchlistAdd,
    user=Depends(get_current_user),
    session: Session = Depends(get_session),
) -> WatchlistItem:
    asset = get_or_create_asset(session, payload.ticker)
    existing = session.scalars(
        select(UserAsset).where(UserAsset.user_id == user.id, UserAsset.asset_id == asset.id)
    ).first()
    if existing:
        return _to_watchlist_item(existing, asset)

    max_order = session.scalar(
        select(func.max(UserAsset.display_order)).where(UserAsset.user_id == user.id)
    ) or 0
    user_asset = UserAsset(user_id=user.id, asset_id=asset.id, display_order=max_order + 1)
    session.add(user_asset)
    session.flush()
    session.refresh(user_asset)
    return _to_watchlist_item(user_asset, asset)


@router.delete("/watchlist/{ticker}", status_code=status.HTTP_204_NO_CONTENT)
def remove_watchlist_item(
    ticker: str,
    user=Depends(get_current_user),
    session: Session = Depends(get_session),
) -> None:
    canonical, _ = resolve_ticker(ticker)
    stmt = (
        select(UserAsset)
        .join(Asset, UserAsset.asset_id == Asset.id)
        .where(UserAsset.user_id == user.id, Asset.ticker == canonical)
    )
    item = session.scalars(stmt).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticker not on watchlist")
    session.delete(item)


@router.put("/watchlist/order", response_model=list[WatchlistItem])
def reorder_watchlist(
    payload: WatchlistOrder,
    user=Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[WatchlistItem]:
    canonical_order: list[str] = []
    for ticker in payload.tickers:
        canonical, _ = resolve_ticker(ticker)
        if canonical not in canonical_order:
            canonical_order.append(canonical)

    if not canonical_order:
        return list_watchlist(user=user, session=session)

    rows = session.execute(
        select(UserAsset, Asset)
        .join(Asset, UserAsset.asset_id == Asset.id)
        .where(UserAsset.user_id == user.id)
    ).all()
    items_by_ticker = {asset.ticker: (user_asset, asset) for user_asset, asset in rows}

    for index, ticker in enumerate(canonical_order, start=1):
        entry = items_by_ticker.get(ticker)
        if entry:
            user_asset, _ = entry
            user_asset.display_order = index
            session.add(user_asset)

    session.flush()
    return list_watchlist(user=user, session=session)
