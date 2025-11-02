from typing import Iterable

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.db.models import Asset, IndicatorSnapshot, MarketSnapshot
from app.db.session import get_session
from app.schemas import IndicatorSnapshotRead, MarketSnapshotRead

router = APIRouter()


def _ticker_filter_clause(stmt: Select, tickers: Iterable[str]) -> Select:
    normalized = [ticker.strip().upper() for ticker in tickers if ticker.strip()]
    if not normalized:
        return stmt
    return stmt.where(Asset.ticker.in_(normalized))


@router.get("/snapshots/latest", response_model=list[MarketSnapshotRead])
def latest_market_snapshots(
    tickers: list[str] | None = Query(default=None, description="Optional list of tickers to filter"),
    session: Session = Depends(get_session),
) -> list[MarketSnapshotRead]:
    latest_subquery = (
        select(
            MarketSnapshot.asset_id.label("asset_id"),
            func.max(MarketSnapshot.as_of).label("max_as_of"),
        )
        .group_by(MarketSnapshot.asset_id)
        .subquery()
    )

    stmt = (
        select(MarketSnapshot, Asset)
        .join(Asset, MarketSnapshot.asset_id == Asset.id)
        .join(
            latest_subquery,
            (MarketSnapshot.asset_id == latest_subquery.c.asset_id)
            & (MarketSnapshot.as_of == latest_subquery.c.max_as_of),
        )
        .order_by(Asset.ticker.asc())
    )

    if tickers:
        stmt = _ticker_filter_clause(stmt, tickers)

    rows = session.execute(stmt).all()
    return [
        MarketSnapshotRead(
            asset_id=market.asset_id,
            ticker=asset.ticker,
            asset_name=asset.name,
            asset_type=asset.type,
            as_of=market.as_of,
            price=market.price,
            price_change_pct=market.price_change_pct,
            volume=market.volume,
            vwap=market.vwap,
            volatility_1d=market.volatility_1d,
        )
        for market, asset in rows
    ]


@router.get("/indicators/latest", response_model=list[IndicatorSnapshotRead])
def latest_indicator_snapshots(
    tickers: list[str] | None = Query(default=None, description="Optional list of tickers to filter"),
    session: Session = Depends(get_session),
) -> list[IndicatorSnapshotRead]:
    latest_subquery = (
        select(
            IndicatorSnapshot.asset_id.label("asset_id"),
            func.max(IndicatorSnapshot.as_of).label("max_as_of"),
        )
        .group_by(IndicatorSnapshot.asset_id)
        .subquery()
    )

    stmt = (
        select(IndicatorSnapshot, Asset)
        .join(Asset, IndicatorSnapshot.asset_id == Asset.id)
        .join(
            latest_subquery,
            (IndicatorSnapshot.asset_id == latest_subquery.c.asset_id)
            & (IndicatorSnapshot.as_of == latest_subquery.c.max_as_of),
        )
        .order_by(Asset.ticker.asc())
    )

    if tickers:
        stmt = _ticker_filter_clause(stmt, tickers)

    rows = session.execute(stmt).all()
    return [
        IndicatorSnapshotRead(
            asset_id=indicator.asset_id,
            ticker=asset.ticker,
            asset_name=asset.name,
            asset_type=asset.type,
            as_of=indicator.as_of,
            rsi_14=indicator.rsi_14,
            macd=indicator.macd,
            macd_signal=indicator.macd_signal,
            atr_14=indicator.atr_14,
        )
        for indicator, asset in rows
    ]
