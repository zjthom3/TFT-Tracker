from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import Select, desc, select
from sqlalchemy.orm import Session

from app.db.models import Asset, PhaseHistory, PhaseState, SentimentObservation
from app.db.session import get_session
from app.schemas import PhaseHistoryRead, PhaseStateRead
from app.dependencies.rate_limit import enforce_rate_limit

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
def list_phase_states(
    tickers: list[str] | None = Query(default=None, description="Optional tickers to filter"),
    session: Session = Depends(get_session),
    _: None = Depends(enforce_rate_limit),
) -> list[PhaseStateRead]:
    stmt: Select = (
        select(PhaseState, Asset)
        .join(Asset, PhaseState.asset_id == Asset.id)
        .order_by(Asset.ticker.asc())
    )

    if tickers:
        normalized = [t.strip().upper() for t in tickers if t.strip()]
        if normalized:
            stmt = stmt.where(Asset.ticker.in_(normalized))
    rows = session.execute(stmt).all()
    asset_ids = [state.asset_id for state, _ in rows]
    sentiment_map: dict[str, tuple[float | None, float | None]] = {}

    if asset_ids:
        observations = session.execute(
            select(SentimentObservation)
            .where(SentimentObservation.asset_id.in_(asset_ids))
            .order_by(SentimentObservation.asset_id, SentimentObservation.observed_at.desc())
        ).scalars().all()

        per_asset: dict[str, list[SentimentObservation]] = {}
        for obs in observations:
            bucket = per_asset.setdefault(str(obs.asset_id), [])
            if len(bucket) < 2:
                bucket.append(obs)

        for asset_id, bucket in per_asset.items():
            latest = bucket[0]
            previous = bucket[1] if len(bucket) > 1 else None
            latest_score = float(latest.score) if latest.score is not None else None
            delta = None
            if latest_score is not None and previous and previous.score is not None:
                delta = float(latest.score - previous.score)
            sentiment_map[asset_id] = (latest_score, delta)

    results: list[PhaseStateRead] = []
    for state, asset in rows:
        sentiment_score, sentiment_delta = sentiment_map.get(str(state.asset_id), (None, None))
        results.append(
            PhaseStateRead(
                asset_id=state.asset_id,
                ticker=asset.ticker,
                display_ticker=asset.display_ticker or asset.ticker,
                asset_name=asset.name,
                asset_type=asset.type,
                phase=state.phase,
                confidence=state.confidence,
                rationale=state.rationale,
                computed_at=state.computed_at,
                sentiment_score=sentiment_score,
                sentiment_delta=sentiment_delta,
            )
        )
    return results


@router.get("/phase/{ticker}", response_model=PhaseStateRead)
def get_phase_state(
    ticker: str,
    session: Session = Depends(get_session),
    _: None = Depends(enforce_rate_limit),
) -> PhaseStateRead:
    asset = _asset_by_ticker(session, ticker)
    state = session.get(PhaseState, asset.id)
    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Phase state not available for {asset.ticker}",
        )

    sentiment_score = None
    sentiment_delta = None
    sentiment_rows = session.execute(
        select(SentimentObservation)
        .where(SentimentObservation.asset_id == asset.id)
        .order_by(SentimentObservation.observed_at.desc())
        .limit(2)
    ).scalars().all()
    if sentiment_rows:
        sentiment_score = float(sentiment_rows[0].score) if sentiment_rows[0].score is not None else None
        if len(sentiment_rows) > 1 and sentiment_rows[0].score is not None and sentiment_rows[1].score is not None:
            sentiment_delta = float(sentiment_rows[0].score - sentiment_rows[1].score)

    return PhaseStateRead(
        asset_id=asset.id,
        ticker=asset.ticker,
        display_ticker=asset.display_ticker or asset.ticker,
        asset_name=asset.name,
        asset_type=asset.type,
        phase=state.phase,
        confidence=state.confidence,
        rationale=state.rationale,
        computed_at=state.computed_at,
        sentiment_score=sentiment_score,
        sentiment_delta=sentiment_delta,
    )


@router.get("/phase/{ticker}/history", response_model=list[PhaseHistoryRead])
def get_phase_history(
    ticker: str,
    limit: int = Query(default=20, ge=1, le=200),
    session: Session = Depends(get_session),
    _: None = Depends(enforce_rate_limit),
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
