from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import Select, desc, select
from sqlalchemy.orm import Session

from app.db.models import Asset, PhaseHistory, PhaseState
from app.db.session import get_session
from app.schemas import PhaseHistoryRead, PhaseStateRead

router = APIRouter()


def _asset_by_ticker(session: Session, ticker: str) -> Asset:
    normalized = ticker.upper()
    asset = session.scalars(select(Asset).where(Asset.ticker == normalized)).first()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset with ticker {normalized} not found",
        )
    return asset


@router.get("/phase", response_model=list[PhaseStateRead])
def list_phase_states(session: Session = Depends(get_session)) -> list[PhaseStateRead]:
    stmt: Select = (
        select(PhaseState, Asset)
        .join(Asset, PhaseState.asset_id == Asset.id)
        .order_by(Asset.ticker.asc())
    )
    rows = session.execute(stmt).all()
    return [
        PhaseStateRead(
            asset_id=state.asset_id,
            ticker=asset.ticker,
            asset_name=asset.name,
            asset_type=asset.type,
            phase=state.phase,
            confidence=state.confidence,
            rationale=state.rationale,
            computed_at=state.computed_at,
        )
        for state, asset in rows
    ]


@router.get("/phase/{ticker}", response_model=PhaseStateRead)
def get_phase_state(ticker: str, session: Session = Depends(get_session)) -> PhaseStateRead:
    asset = _asset_by_ticker(session, ticker)
    state = session.get(PhaseState, asset.id)
    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Phase state not available for {asset.ticker}",
        )

    return PhaseStateRead(
        asset_id=asset.id,
        ticker=asset.ticker,
        asset_name=asset.name,
        asset_type=asset.type,
        phase=state.phase,
        confidence=state.confidence,
        rationale=state.rationale,
        computed_at=state.computed_at,
    )


@router.get("/phase/{ticker}/history", response_model=list[PhaseHistoryRead])
def get_phase_history(
    ticker: str,
    limit: int = Query(default=20, ge=1, le=200),
    session: Session = Depends(get_session),
    since_minutes: Optional[int] = Query(default=None, ge=1),
) -> list[PhaseHistoryRead]:
    asset = _asset_by_ticker(session, ticker)

    stmt = (
        select(PhaseHistory)
        .where(PhaseHistory.asset_id == asset.id)
        .order_by(desc(PhaseHistory.changed_at))
        .limit(limit)
    )

    if since_minutes is not None:
        window_start = datetime.now(timezone.utc) - timedelta(minutes=since_minutes)
        stmt = stmt.where(PhaseHistory.changed_at >= window_start)

    history_rows = session.scalars(stmt).all()
    return [
        PhaseHistoryRead(
            id=entry.id,
            asset_id=entry.asset_id,
            ticker=asset.ticker,
            from_phase=entry.from_phase,
            to_phase=entry.to_phase,
            confidence=entry.confidence,
            rationale=entry.rationale,
            changed_at=entry.changed_at,
        )
        for entry in history_rows
    ]
