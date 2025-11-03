from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Asset
from app.utils.tickers import resolve_ticker


def get_or_create_asset(
    session: Session,
    raw_ticker: str,
    *,
    asset_type_hint: Optional[str] = None,
    name: Optional[str] = None,
    exchange: Optional[str] = None,
) -> Asset:
    canonical, display = resolve_ticker(raw_ticker)
    stmt = select(Asset).where(Asset.ticker == canonical)
    asset = session.scalars(stmt).first()
    if asset:
        updated = False
        if display and asset.display_ticker != display:
            asset.display_ticker = display
            updated = True
        if name and asset.name != name:
            asset.name = name
            updated = True
        if exchange and asset.exchange != exchange:
            asset.exchange = exchange
            updated = True
        if updated:
            session.add(asset)
        return asset

    asset = Asset(
        ticker=canonical,
        display_ticker=display,
        name=name,
        exchange=exchange,
        type=asset_type_hint or ("crypto" if canonical.endswith("-USD") else "stock"),
    )
    session.add(asset)
    session.flush()
    session.refresh(asset)
    return asset
