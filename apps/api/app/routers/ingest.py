from typing import Sequence

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import Asset
from app.db.session import get_session
from app.schemas import IngestResult
from app.services.classify_phase import PhaseUpdateService
from app.services.ingest_market import MarketIngestor
from app.services.sentiment import SentimentIngestor, SentimentSummary
from app.dependencies.rate_limit import enforce_rate_limit

router = APIRouter()


@router.post("/run", response_model=Sequence[IngestResult])
def run_ingest(
    session: Session = Depends(get_session),
    _: None = Depends(enforce_rate_limit),
) -> Sequence[IngestResult]:
    settings = get_settings()
    ingestor = MarketIngestor(session=session, window_days=settings.ingest_window_days)
    summaries = ingestor.ingest_many(settings.ingest_tickers)
    sentiment_summaries: list[SentimentSummary] = []
    if settings.enable_sentiment:
        sentiment_summaries = SentimentIngestor(
            session=session, window_minutes=settings.sentiment_window_minutes
        ).ingest_many(settings.ingest_tickers)
    phase_states = PhaseUpdateService(session).update_assets_by_ticker(settings.ingest_tickers)

    phase_by_ticker = {}
    for state in phase_states:
        asset = session.get(Asset, state.asset_id)
        if asset:
            phase_by_ticker[asset.ticker] = state

    sentiment_by_ticker = {summary.ticker: summary for summary in sentiment_summaries}

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
                sentiment_score=(
                    round(sentiment_by_ticker[summary.ticker].average_score, 4)
                    if summary.ticker in sentiment_by_ticker and sentiment_by_ticker[summary.ticker].average_score is not None
                    else None
                ),
            )
        )
    return results
