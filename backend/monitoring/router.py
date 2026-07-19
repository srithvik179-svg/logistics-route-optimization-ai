"""Monitoring and observability router exposing health checks, telemetry metrics, and diagnostic reports."""

from fastapi import APIRouter, Depends
from backend.models.health_status import SystemHealthReport
from backend.models.metric_snapshot import MetricSnapshot
from backend.models.diagnostic_report import DiagnosticReport
from backend.monitoring.telemetry_manager import TelemetryManager
from backend.monitoring.diagnostics import DiagnosticsService
from backend.security.authorization import require_permission
from backend.models.security_context import UserPrincipal

monitoring_router = APIRouter(prefix="/api/v1/monitoring", tags=["Monitoring"])


@monitoring_router.get("/health", response_model=SystemHealthReport)
def get_system_health(
    current_user: UserPrincipal = Depends(require_permission("system:read"))
):
    """Retrieves cached system and services health check reports."""
    return TelemetryManager.get_cached_health()


@monitoring_router.get("/metrics", response_model=MetricSnapshot)
def get_system_metrics(
    current_user: UserPrincipal = Depends(require_permission("system:read"))
):
    """Retrieves runtime telemetry metrics and cache hit statistics."""
    return TelemetryManager.generate_telemetry_snapshot()


@monitoring_router.get("/diagnostics", response_model=DiagnosticReport)
def get_system_diagnostics(
    current_user: UserPrincipal = Depends(require_permission("system:read"))
):
    """Generates analytical diagnostics pinpointing bottlenecks or failure profiles."""
    return DiagnosticsService.generate_report()
