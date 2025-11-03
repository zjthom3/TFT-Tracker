import asyncio
import logging

from app.config import get_settings
from app.db.session import SessionLocal
from app.services.classify_phase import PhaseUpdateService
from app.services.ingest_market import MarketIngestor
from app.services.sentiment import SentimentIngestor

log = logging.getLogger(__name__)


async def poll_market_data() -> None:
    settings = get_settings()
    interval = settings.ingest_interval_minutes * 60
    while True:
        try:
            with SessionLocal() as session:
                ingestor = MarketIngestor(session=session, window_days=settings.ingest_window_days)
                summaries = ingestor.ingest_many(settings.ingest_tickers)
                if settings.enable_sentiment:
                    SentimentIngestor(session=session, window_minutes=settings.sentiment_window_minutes).ingest_many(
                        settings.ingest_tickers
                    )
                PhaseUpdateService(session).update_assets_by_ticker(settings.ingest_tickers)
                session.commit()
                log.debug("Ingest summaries: %s", summaries)
        except Exception as exc:  # pragma: no cover - background logging
            log.exception("Scheduled ingest failed: %s", exc)
        await asyncio.sleep(interval)
