from fastapi.testclient import TestClient

from main import app  # adjust import to match your actual FastAPI app entrypoint

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200


def test_health_ready():
    response = client.get("/health/ready")
    # 503 is a valid outcome here too — Postgres/Redis may not be reachable
    # from this test environment. What matters is the shape of the response.
    assert response.status_code in (200, 503)
    body = response.json()
    assert "postgres" in body
    assert "redis" in body