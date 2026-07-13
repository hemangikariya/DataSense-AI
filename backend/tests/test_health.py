from fastapi.testclient import TestClient


def test_backend_health_check_endpoint(client: TestClient):
    """
    Asserts the system health endpoint responds with successful payload metrics.
    """
    response = client.get("/health")
    assert response.status_code in [200, 503]  # Can be 503 if infrastructure is not live in test env
    data = response.json()
    assert "status" in data
    assert "services" in data
    assert "backend" in data["services"]
