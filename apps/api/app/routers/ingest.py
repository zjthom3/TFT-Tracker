from typing import Sequence

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import Asset
from app.db.session import get_session
from app.schemas import IngestResult
from app.services.classify_phase import PhaseUpdateService
from app.services.ingest_market import MarketIngestor

router = APIRouter()


@router.post("/run", response_model=Sequence[IngestResult])
def run_ingest(session: Session = Depends(get_session)) -> Sequence[IngestResult]:
    settings = get_settings()
    ingestor = MarketIngestor(session=session, window_days=settings.ingest_window_days)
    summaries = ingestor.ingest_many(settings.ingest_tickers)
    phase_states = PhaseUpdateService(session).update_assets_by_ticker(settings.ingest_tickers)

    phase_by_ticker = {}
    for state in phase_states:
        asset = session.get(Asset, state.asset_id)
        if asset:
            phase_by_ticker[asset.ticker] = state

    results = []
    for summary in summaries:
        state = phase_by_ticker.get(summary.ticker)
        results.append(
            IngestResult(
                ticker=summary.ticker,
                ingested_at=summary.ingested_at,
                market_records=summary.market_records,
                indicator_records=summary.indicator_records,
                phase=state.phase if state else None,
                phase_confidence=state.confidence if state else None,
            )
        )
    return results
