from datetime import datetime, timezone
from typing import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.db.models import Base, SentimentObservation, SentimentSource
from app.services.sentiment import SentimentIngestor


class DummySentimentIngestor(SentimentIngestor):
    def _fetch_recent_news(self, ticker: str):  # type: ignore[override]
        now = datetime.now(timezone.utc)
        return [
            {
                "title": f"{ticker} surges on optimism",
                "summary": "positive outlook",
                "providerPublishTime": int(now.timestamp()),
            },
            {
                "title": f"{ticker} facing mild correction",
                "summary": "mixed signals",
                "providerPublishTime": int(now.timestamp()),
            },
        ]


@pytest.fixture()
def engine():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture()
def session(engine) -> Iterator[Session]:
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_sentiment_ingestor_persists_observation(session: Session) -> None:
    settings = get_settings()
    assert settings.enable_sentiment is True

    ingestor = DummySentimentIngestor(session=session, window_minutes=60)
    summary = ingestor.ingest_single("NVDA")
    session.commit()

    assert summary is not None
    assert summary.ticker == "NVDA"
    assert summary.observations == 2
    assert summary.average_score is not None

    sources = session.query(SentimentSource).all()
    assert len(sources) == 1
    observations = session.query(SentimentObservation).all()
    assert len(observations) == 1

    new_summary = ingestor.ingest_single("NVDA")
    session.commit()
    assert new_summary is not None
    observations_after = session.query(SentimentObservation).all()
    assert len(observations_after) == 1
