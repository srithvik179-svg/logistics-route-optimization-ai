"""API Gateway router exposing health check, service registries, and system statistics."""

from fastapi import APIRouter
from backend.services.api_registry import APIRegistry

gateway_router = APIRouter(prefix="/api/v1/gateway", tags=["Gateway"])


@gateway_router.get("/health")
def get_health():
    """Returns application engine health status indicators."""
    return APIRegistry.get_system_health()


@gateway_router.get("/services")
def get_services():
    """Returns registered services registry."""
    return APIRegistry.get_registered_services()


@gateway_router.get("/stats")
def get_stats():
    """Returns system statistics."""
    return APIRegistry.get_system_statistics()
