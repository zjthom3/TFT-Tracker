from datetime import datetime, timedelta, timezone
from typing import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Asset, Base, IndicatorSnapshot, MarketSnapshot, PhaseHistory
from app.db.session import get_session
from app.main import create_app
from app.services.classify_phase import PhaseUpdateService, PHASE_COOP, PHASE_DEFECT, PHASE_FORGIVE


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
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


def _market_snapshot(asset_id, price, price_change, volatility, as_of):
    return MarketSnapshot(
        asset_id=asset_id,
        price=price,
        price_change_pct=price_change,
        volume=1_000_000,
        vwap=price,
        volatility_1d=volatility,
        as_of=as_of,
    )


def _indicator_snapshot(asset_id, market_snapshot_id, rsi, macd, macd_signal, atr, as_of):
    return IndicatorSnapshot(
        asset_id=asset_id,
        market_snapshot_id=market_snapshot_id,
        rsi_14=rsi,
        macd=macd,
        macd_signal=macd_signal,
        atr_14=atr,
        as_of=as_of,
    )


def test_defection_phase_detection(session: Session) -> None:
    now = datetime.now(timezone.utc)
    asset = Asset(ticker="NVDA", name="NVIDIA", type="stock")
    session.add(asset)
    session.flush()

    older = _market_snapshot(asset.id, price=430.0, price_change=None, volatility=1.5, as_of=now - timedelta(hours=1))
    session.add(older)
    session.flush()
    session.add(_indicator_snapshot(asset.id, older.id, rsi=55, macd=0.4, macd_signal=0.3, atr=2.0, as_of=older.as_of))

    current = _market_snapshot(asset.id, price=410.0, price_change=-4.65, volatility=2.1, as_of=now)
    session.add(current)
    session.flush()
    session.add(_indicator_snapshot(asset.id, current.id, rsi=28, macd=-1.1, macd_signal=-0.8, atr=2.5, as_of=current.as_of))
    session.commit()

    service = PhaseUpdateService(session)
    state = service.update_asset(asset)
    session.commit()

    assert state is not None
    assert state.phase == PHASE_DEFECT
    assert state.confidence and state.confidence >= 0.7
    history_rows = session.query(PhaseHistory).filter(PhaseHistory.asset_id == asset.id).all()
    assert len(history_rows) == 1
    assert history_rows[0].to_phase == PHASE_DEFECT


def test_forgiveness_after_defection(session: Session) -> None:
    now = datetime.now(timezone.utc)
    asset = Asset(ticker="BTC-USD", name="Bitcoin", type="crypto")
    session.add(asset)
    session.flush()

    # Seed defection history
    defect_market = _market_snapshot(asset.id, price=60000, price_change=-3.0, volatility=4.0, as_of=now - timedelta(hours=2))
    session.add(defect_market)
    session.flush()
    session.add(_indicator_snapshot(asset.id, defect_market.id, rsi=30, macd=-1.5, macd_signal=-1.2, atr=1500, as_of=defect_market.as_of))
    session.commit()

    service = PhaseUpdateService(session)
    service.update_asset(asset)
    session.commit()

    # Now provide stabilizing data
    calm_market = _market_snapshot(asset.id, price=60100, price_change=0.1, volatility=3.5, as_of=now - timedelta(hours=1))
    session.add(calm_market)
    session.flush()
    session.add(_indicator_snapshot(asset.id, calm_market.id, rsi=42, macd=-0.5, macd_signal=-0.3, atr=1200, as_of=calm_market.as_of))

    latest_market = _market_snapshot(asset.id, price=60200, price_change=0.15, volatility=3.2, as_of=now)
    session.add(latest_market)
    session.flush()
    session.add(_indicator_snapshot(asset.id, latest_market.id, rsi=46, macd=-0.2, macd_signal=-0.1, atr=1100, as_of=latest_market.as_of))
    session.commit()

    state = service.update_asset(asset)
    session.commit()

    assert state is not None
    assert state.phase == PHASE_FORGIVE
    history_rows = session.query(PhaseHistory).filter(PhaseHistory.asset_id == asset.id).all()
    assert history_rows[-1].to_phase == PHASE_FORGIVE


def test_cooperation_when_signals_neutral(session: Session) -> None:
    now = datetime.now(timezone.utc)
    asset = Asset(ticker="ETH-USD", name="Ethereum", type="crypto")
    session.add(asset)
    session.flush()

    earlier = _market_snapshot(asset.id, price=3200, price_change=None, volatility=2.5, as_of=now - timedelta(hours=1))
    session.add(earlier)
    session.flush()
    session.add(_indicator_snapshot(asset.id, earlier.id, rsi=48, macd=0.1, macd_signal=0.05, atr=90, as_of=earlier.as_of))

    latest = _market_snapshot(asset.id, price=3220, price_change=0.5, volatility=2.2, as_of=now)
    session.add(latest)
    session.flush()
    session.add(_indicator_snapshot(asset.id, latest.id, rsi=52, macd=0.2, macd_signal=0.15, atr=85, as_of=latest.as_of))
    session.commit()

    state = PhaseUpdateService(session).update_asset(asset)
    session.commit()

    assert state is not None
    assert state.phase == PHASE_COOP
    assert state.confidence and state.confidence >= 0.6


def test_phase_endpoints_with_classification(engine) -> None:
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = TestingSession()

    now = datetime.now(timezone.utc)
    asset = Asset(ticker="NVDA", name="NVIDIA", type="stock")
    session.add(asset)
    session.flush()

    market = _market_snapshot(asset.id, price=420, price_change=-2.5, volatility=1.8, as_of=now)
    session.add(market)
    session.flush()
    session.add(_indicator_snapshot(asset.id, market.id, rsi=30, macd=-0.7, macd_signal=-0.5, atr=1.9, as_of=market.as_of))
    session.commit()

    PhaseUpdateService(session).update_asset(asset)
    session.commit()
    session.close()

    app = create_app(init_db=False)

    def override_session() -> Iterator[Session]:
        with TestingSession() as override:
            yield override

    app.dependency_overrides[get_session] = override_session

    client = TestClient(app)
    response = client.get("/phase")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["phase"] == PHASE_DEFECT

    detail = client.get("/phase/NVDA").json()
    assert detail["ticker"] == "NVDA"

    history = client.get("/phase/NVDA/history").json()
    assert history and history[0]["to_phase"] == PHASE_DEFECT
