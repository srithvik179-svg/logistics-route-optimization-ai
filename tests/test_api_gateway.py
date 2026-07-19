"""Verification test suite for the Enterprise API Gateway (Phase 26).

Tests response formatting, request tracing, global exception mapping, and registry metadata.
"""

import os
import sys
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.services.repository import repository
from backend.main import app


def setup():
    """Initialize repository for tests."""
    if not repository.is_initialized():
        repository.initialize()


def test_standard_response_envelope():
    """Verify that all API JSON endpoints are wrapped in standard APIResponse envelopes."""
    print("\n--- TESTING GATEWAY ENVELOPE ---")
    client = TestClient(app)
    response = client.get("/api/v1/gateway/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert data["status"] == "success"
    assert "message" in data
    assert "timestamp" in data
    assert "request_id" in data
    assert len(data["request_id"]) == 36  # UUID length
    assert "execution_time_ms" in data
    assert "payload" in data
    assert "error" in data
    assert data["error"] is None

    payload = data["payload"]
    assert payload["overall_status"] == "UP"
    assert payload["services_count"] > 0
    print("✓ Gateway envelope verified.")


def test_registry_metadata():
    """Verify that registered services are correctly returned."""
    print("\n--- TESTING SERVICE REGISTRY ---")
    client = TestClient(app)
    response = client.get("/api/v1/gateway/services")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    
    services = data["payload"]
    assert len(services) > 0
    names = [s["name"] for s in services]
    assert "Ant Colony Optimization Engine" in names
    assert "AI Decision Support Preparation Engine" in names
    print("✓ Service registry verified.")


def test_validation_error_handler():
    """Verify that pydantic model validation failures return standard error envelopes."""
    print("\n--- TESTING VALIDATION ERROR HANDLER ---")
    client = TestClient(app)
    # Post empty or invalid body to route scoring payload route
    response = client.post("/api/route-scoring/payload", json={"filters": "INVALID_TYPE"})
    
    assert response.status_code == 422
    data = response.json()
    
    assert data["status"] == "error"
    assert data["payload"] is None
    assert data["error"] is not None
    
    err = data["error"]
    assert err["code"] == 422
    assert err["type"] == "ValidationError"
    assert "filters" in err["detail"]
    print("✓ Validation exception handler verified.")


def test_not_found_error_handler():
    """Verify that missing routes return HTTP exceptions in standardized envelope."""
    print("\n--- TESTING HTTP ERROR HANDLER ---")
    client = TestClient(app)
    response = client.get("/api/non-existent-route-path")
    
    assert response.status_code == 404
    data = response.json()
    
    assert data["status"] == "error"
    assert data["error"] is not None
    err = data["error"]
    assert err["code"] == 404
    assert "Not Found" in err["detail"]
    print("✓ HTTP exception handler verified.")


if __name__ == "__main__":
    print("Initializing Enterprise API Gateway verification suite...")
    setup()

    test_standard_response_envelope()
    test_registry_metadata()
    test_validation_error_handler()
    test_not_found_error_handler()

    print("\n" + "=" * 60)
    print("All Enterprise API Gateway tests passed successfully!")
    print("=" * 60)
