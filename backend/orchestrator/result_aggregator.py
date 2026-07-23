"""Result Aggregator — Aggregates real metrics and payloads from all existing workspace services."""

from typing import Dict, Any

from backend.services.corridor_service import CorridorService
from backend.services.simulation_service import SimulationService
from backend.services.reverse_logistics_service import ReverseLogisticsService
from backend.services.sla_prediction_service import SLAPredictionService
from backend.services.risk_forecasting_service import RiskForecastingService

class ResultAggregator:
    """Invokes existing analytics modules to retrieve concrete logistics workspace parameters."""

    @classmethod
    def aggregate_data(cls, filters: Dict[str, Any]) -> Dict[str, Any]:
        # Collect outputs safely from existing engines
        try:
            corridor_payload = CorridorService.get_corridor_intelligence(filters)
        except Exception:
            corridor_payload = {"corridors": [], "summary": {}}

        try:
            simulation_payload = SimulationService.get_simulation_payload(filters, {})
        except Exception:
            simulation_payload = {"summary": {}, "recommendations": []}

        try:
            reverse_payload = ReverseLogisticsService.get_reverse_logistics(filters)
        except Exception:
            reverse_payload = {"returns": [], "analytics": {}}

        try:
            sla_payload = SLAPredictionService.get_prediction_payload(filters)
        except Exception:
            sla_payload = {"shipments": [], "summary": {}, "recommendations": []}

        try:
            forecast_payload = RiskForecastingService.get_forecast_payload(filters)
        except Exception:
            forecast_payload = {"timeline": []}

        return {
            "corridors": corridor_payload,
            "simulation": simulation_payload,
            "reverse_logistics": reverse_payload,
            "sla_prediction": sla_payload,
            "risk_forecast": forecast_payload
        }
