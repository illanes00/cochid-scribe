"""Tests for health endpoint."""


def test_health_check(client):
    """Test the simple health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_api_health_check_simple(client):
    """Test the API health check simple endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "host" in data


def test_api_health_check_detailed(client):
    """Test the detailed health check endpoint."""
    response = client.get("/api/v1/health/detailed")
    assert response.status_code == 200
    data = response.json()

    # Check top-level fields
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
    assert data["service"] == "Scribe API"
    assert "environment" in data
    assert "host" in data
    assert "timestamp" in data
    assert "components" in data

    # Check component statuses
    components = data["components"]
    assert "database" in components
    assert "google_integration" in components
    assert "llm_service" in components

    # Database should always be healthy in tests
    assert components["database"]["status"] == "healthy"
    assert "latency_ms" in components["database"]

    # Google and LLM may be degraded if not configured
    for component in components.values():
        assert component["status"] in ["healthy", "degraded", "unhealthy"]
        assert "message" in component
