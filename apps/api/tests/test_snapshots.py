from datetime import datetime, timedelta, timezone
from typing import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import Asset, Base, IndicatorSnapshot, MarketSnapshot
from app.db.session import get_session
from app.main import create_app
from app.dependencies.rate_limit import enforce_rate_limit


@pytest.fixture()
def client() -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(engine)

    app = create_app(init_db=False)

    def override_get_session() -> Iterator[Session]:
        session = TestingSession()
        try:
            yield session
            session.commit()
        finally:
            session.close()

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[enforce_rate_limit] = lambda: None

    with TestingSession() as session:
        seed_snapshot_data(session)

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_session, None)
    app.dependency_overrides.pop(enforce_rate_limit, None)


def seed_snapshot_data(session: Session) -> None:
    now = datetime.now(tz=timezone.utc)
    one_hour = timedelta(hours=1)

    asset_nvda = Asset(ticker="NVDA", name="NVIDIA Corporation", type="stock", exchange="NASDAQ")
    asset_btc = Asset(ticker="BTC-USD", name="Bitcoin", type="crypto", exchange="CRYPTO")
    session.add_all([asset_nvda, asset_btc])
    session.flush()

    # Older snapshot for NVDA to ensure only latest returned.
    older_nvda_snapshot = MarketSnapshot(
        asset_id=asset_nvda.id,
        price=420.50,
        price_change_pct=-0.5,
        volume=1_000_000,
        vwap=419.80,
        volatility_1d=1.2,
        as_of=now - one_hour,
    )
    session.add(older_nvda_snapshot)
    session.flush()

    latest_nvda_snapshot = MarketSnapshot(
        asset_id=asset_nvda.id,
        price=425.12,
        price_change_pct=1.05,
        volume=1_200_000,
        vwap=424.90,
        volatility_1d=1.1,
        as_of=now,
    )
    session.add(latest_nvda_snapshot)
    session.flush()

    session.add_all(
        [
            IndicatorSnapshot(
                asset_id=asset_nvda.id,
                market_snapshot_id=older_nvda_snapshot.id,
                rsi_14=55.0,
                macd=0.8,
                macd_signal=0.6,
                atr_14=2.5,
                as_of=older_nvda_snapshot.as_of,
            ),
            IndicatorSnapshot(
                asset_id=asset_nvda.id,
                market_snapshot_id=latest_nvda_snapshot.id,
                rsi_14=60.0,
                macd=0.9,
                macd_signal=0.7,
                atr_14=2.6,
                as_of=latest_nvda_snapshot.as_of,
            ),
        ]
    )

    btc_snapshot = MarketSnapshot(
        asset_id=asset_btc.id,
        price=64000.0,
        price_change_pct=2.1,
        volume=15_000,
        vwap=63950.0,
        volatility_1d=3.4,
        as_of=now - timedelta(minutes=30),
    )
    session.add(btc_snapshot)
    session.flush()

    session.add(
        IndicatorSnapshot(
            asset_id=asset_btc.id,
            market_snapshot_id=btc_snapshot.id,
            rsi_14=48.5,
            macd=-1.2,
            macd_signal=-0.8,
            atr_14=1200.0,
            as_of=btc_snapshot.as_of,
        )
    )

    session.commit()


def test_latest_market_snapshots_returns_only_newest_rows(client: TestClient) -> None:
    response = client.get("/snapshots/latest")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    tickers = [entry["ticker"] for entry in data]
    assert tickers == sorted(tickers)
    nvda_entry = next(item for item in data if item["ticker"] == "NVDA")
    assert nvda_entry["price"] == 425.12
    assert nvda_entry["price_change_pct"] == 1.05


def test_latest_market_snapshots_filter_by_ticker(client: TestClient) -> None:
    response = client.get("/snapshots/latest", params={"tickers": ["nvda"]})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["ticker"] == "NVDA"


def test_latest_indicator_snapshots(client: TestClient) -> None:
    response = client.get("/indicators/latest")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    nvda_entry = next(item for item in data if item["ticker"] == "NVDA")
    assert nvda_entry["rsi_14"] == 60.0
    assert nvda_entry["macd_signal"] == 0.7
