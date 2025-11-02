from typing import Sequence

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.session import get_session
from app.schemas import IngestResult
from app.services.ingest_market import MarketIngestor

router = APIRouter()


@router.post("/run", response_model=Sequence[IngestResult])
def run_ingest(session: Session = Depends(get_session)) -> Sequence[IngestResult]:
    settings = get_settings()
    ingestor = MarketIngestor(session=session, window_days=settings.ingest_window_days)
    summaries = ingestor.ingest_many(settings.ingest_tickers)
    results = [
        IngestResult(
            ticker=summary.ticker,
            ingested_at=summary.ingested_at,
            market_records=summary.market_records,
            indicator_records=summary.indicator_records,
        )
        for summary in summaries
    ]
    return results
