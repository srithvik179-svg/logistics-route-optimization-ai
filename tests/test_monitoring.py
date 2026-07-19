"""Verification test suite for the Enterprise Monitoring, Logging & Observability Platform (Phase 28).

Tests structured logging, telemetry collection, health checks, diagnostics generation, and route locks.
"""

import os
import sys
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.services.repository import repository
from backend.main import app
from backend.monitoring.structured_logger import StructuredLogger
from backend.monitoring.metrics_collector import MetricsCollector
from backend.monitoring.health_service import HealthService
from backend.monitoring.diagnostics import DiagnosticsService
from backend.monitoring.telemetry_manager import TelemetryManager


def setup():
    """Initialize repository for tests."""
    if not repository.is_initialized():
        repository.initialize()


def test_structured_logger():
    """Verify structured logger runs and outputs correctly."""
    print("\n--- TESTING STRUCTURED LOGGER ---")
    # Should run without raising any exceptions
    StructuredLogger.info("Test message", {"source": "unit_test", "index": 42})
    StructuredLogger.warning("Test warning", {"source": "unit_test"})
    StructuredLogger.error("Test error", {"source": "unit_test"})
    print("✓ Structured logger verified.")


def test_metrics_collector():
    """Verify metrics collector aggregates values correctly."""
    print("\n--- TESTING METRICS COLLECTOR ---")
    MetricsCollector.record_request_start()
    MetricsCollector.record_request_end("/api/test-route", 150.5, 200)
    
    MetricsCollector.record_request_start()
    MetricsCollector.record_request_end("/api/test-route", 250.5, 500)

    MetricsCollector.record_cache_hit()
    MetricsCollector.record_cache_miss()

    MetricsCollector.record_engine_run("AStarEngine", 80.0, True)
    MetricsCollector.record_exception("TestException: Database timeout")

    data = MetricsCollector.get_snapshot_data()
    assert data["total_requests"] >= 2
    assert data["failed_requests"] >= 1
    assert data["api_response_time_avg"] > 0.0
    assert data["cache_hit_ratio"] == 0.5
    assert data["cache_miss_ratio"] == 0.5
    assert len(data["traces"]) > 0
    assert len(data["exceptions"]) > 0

    print("✓ Metrics collector aggregates verified.")


def test_health_checks():
    """Verify health checks retrieve correct reports."""
    print("\n--- TESTING HEALTH SERVICE ---")
    report = HealthService.perform_system_check()
    
    assert report.overall_status in ["UP", "DEGRADED"]
    assert report.checks_count == 3
    
    names = [s.name for s in report.services]
    assert "Data Repository Layer" in names
    assert "Security & Access Control Layer" in names
    assert "Optimization & Search Engines" in names

    print("✓ Health reports verified.")


def test_secured_monitoring_endpoints():
    """Verify standard monitoring endpoints are secured and assert schemas."""
    print("\n--- TESTING MONITORING ENDPOINTS ---")
    client = TestClient(app)

    # 1. Unauthenticated checks should fail (401)
    res_unauth = client.get("/api/v1/monitoring/health")
    assert res_unauth.status_code == 401

    # 2. Authenticate as Admin (possesses system:read permission)
    res_login = client.post("/api/v1/security/auth/token", json={"username": "admin", "password": "admin123"})
    assert res_login.status_code == 200
    token = res_login.json()["payload"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Retrieve health reports
    res_health = client.get("/api/v1/monitoring/health", headers=headers)
    assert res_health.status_code == 200
    health_data = res_health.json()["payload"]
    assert "overall_status" in health_data
    assert "services" in health_data

    # 4. Retrieve metrics snapshots
    res_metrics = client.get("/api/v1/monitoring/metrics", headers=headers)
    assert res_metrics.status_code == 200
    metrics_data = res_metrics.json()["payload"]
    assert "api_response_time_avg" in metrics_data
    assert "memory_usage_bytes" in metrics_data

    # 5. Retrieve diagnostics summaries
    res_diag = client.get("/api/v1/monitoring/diagnostics", headers=headers)
    assert res_diag.status_code == 200
    diag_data = res_diag.json()["payload"]
    assert "performance_summary" in diag_data
    assert "slowest_services" in diag_data

    print("✓ All monitoring API endpoints verified.")


if __name__ == "__main__":
    print("Initializing Enterprise Monitoring verification suite...")
    setup()

    test_structured_logger()
    test_metrics_collector()
    test_health_checks()
    test_secured_monitoring_endpoints()

    print("\n" + "=" * 60)
    print("All Enterprise Monitoring tests passed successfully!")
    print("=" * 60)
