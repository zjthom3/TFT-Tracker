from fastapi.testclient import TestClient

from app.main import create_app


client = TestClient(create_app(init_db=False))


def test_healthcheck() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
