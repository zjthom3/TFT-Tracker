import asyncio
import logging

from sqlalchemy import select

from app.config import get_settings
from app.db.models import Asset
from app.db.session import SessionLocal
from app.services.classify_phase import PhaseUpdateService
from app.services.ingest_market import MarketIngestor
from app.services.sentiment import SentimentIngestor
from app.utils.tickers import resolve_ticker

log = logging.getLogger(__name__)


async def poll_market_data() -> None:
    settings = get_settings()
    interval = settings.ingest_interval_minutes * 60
    while True:
        try:
            with SessionLocal() as session:
                asset_rows = session.execute(select(Asset.ticker)).all()
                dynamic_tickers = {row[0] for row in asset_rows if row[0]}
                for ticker in settings.ingest_tickers:
                    if ticker and ticker.strip():
                        canonical, _ = resolve_ticker(ticker)
                        dynamic_tickers.add(canonical)
                tickers = sorted(dynamic_tickers)
                if not tickers:
                    await asyncio.sleep(interval)
                    continue

                ingestor = MarketIngestor(session=session, window_days=settings.ingest_window_days)
                summaries = ingestor.ingest_many(tickers)
                if settings.enable_sentiment:
                    SentimentIngestor(session=session, window_minutes=settings.sentiment_window_minutes).ingest_many(
                        tickers
                    )
                PhaseUpdateService(session).update_assets_by_ticker(tickers)
                session.commit()
                log.debug("Ingest summaries: %s", summaries)
        except Exception as exc:  # pragma: no cover - background logging
            log.exception("Scheduled ingest failed: %s", exc)
        await asyncio.sleep(interval)
