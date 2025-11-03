from __future__ import annotations

from typing import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Base
from app.db.session import get_session
from app.dependencies.rate_limit import enforce_rate_limit, rate_limiter
from app.main import create_app


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


@pytest.fixture()
def client(session: Session, engine) -> Iterator[TestClient]:
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def override_session() -> Iterator[Session]:
        db = TestingSession()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    app = create_app(init_db=False)
    original_limit = rate_limiter.max_requests
    rate_limiter.max_requests = 1000

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[enforce_rate_limit] = lambda: None

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_session, None)
    app.dependency_overrides.pop(enforce_rate_limit, None)
    rate_limiter.max_requests = original_limit


def test_watchlist_alias_flow(client: TestClient) -> None:
    guest_resp = client.post("/auth/guest")
    assert guest_resp.status_code == 201
    token = guest_resp.json()["session_token"]
    headers = {"X-Session-Token": token}

    add_resp = client.post("/watchlist", json={"ticker": "TRUMP-USD"}, headers=headers)
    assert add_resp.status_code == 201
    add_payload = add_resp.json()
    assert add_payload["ticker"] == "TRUMP35336-USD"
    assert add_payload["display_ticker"] == "TRUMP-USD"

    list_resp = client.get("/watchlist", headers=headers)
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert len(items) == 1

    order_resp = client.put(
        "/watchlist/order",
        json={"tickers": ["TRUMP35336-USD"]},
        headers=headers,
    )
    assert order_resp.status_code == 200

    delete_resp = client.delete("/watchlist/TRUMP-USD", headers=headers)
    assert delete_resp.status_code == 204
    list_resp = client.get("/watchlist", headers=headers)
    assert list_resp.status_code == 200
    assert list_resp.json() == []
