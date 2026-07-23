from typing import Dict, Any, List
import pandas as pd

from backend.services.route_analysis_service import RouteAnalysisService
from backend.services.route_decision_engine import RouteDecisionEngine
from backend.services.repository import repository
from backend.analytics.corridor_metrics import CorridorMetrics
from backend.utils.logger import logger

class CorridorService:
    """Service providing corridor analysis payloads and strategic recommendations."""

    @classmethod
    def get_corridor_intelligence(cls, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Compiles scoring data, highlights bottlenecks, drafts optimization suggestions, and runs AI decision engine.
        
        Args:
            filters: Global filters dictionary.
            
        Returns:
            Dict containing detailed corridor analytics and AI decision intelligence.
        """
        logger.info("CorridorService: Fetching corridor intelligence payload.")

        # 1. Fetch raw datasets for decision engine
        df_tx = repository._processed_sheets.get("Logistics_Transactions")
        df_hub = repository._processed_sheets.get("Hub_Location_Master")
        tpr_sheet_name = "TPR_Master" if repository.sheet_exists("TPR_Master") else "Repair_Center_Master"
        df_tpr = repository._processed_sheets.get(tpr_sheet_name)

        if df_tx is None or len(df_tx) == 0:
            df_tx = pd.DataFrame()
        if df_hub is None:
            df_hub = pd.DataFrame()
        if df_tpr is None:
            df_tpr = pd.DataFrame()

        # 2. Run Centralized AI Route Decision Engine
        decision_payload = RouteDecisionEngine.evaluate_all_corridors(df_tx, df_hub, df_tpr)

        # 3. Fetch legacy routes for backward compatibility
        analysis = RouteAnalysisService.get_route_analysis_payload(filters)
        raw_routes = analysis.get("routes", [])
        enriched_routes = CorridorMetrics.calculate_corridor_scores(raw_routes)

        if not enriched_routes and len(decision_payload.get("corridors", [])) > 0:
            # Map decision engine corridors to legacy enriched format
            enriched_routes = []
            for c in decision_payload["corridors"]:
                parts = c["corridor_id"].split(" → ")
                enriched_routes.append({
                    "origin": parts[0] if len(parts) > 0 else "HUB-A",
                    "destination": parts[1] if len(parts) > 1 else "HUB-B",
                    "distance": c["metrics"]["avg_distance"],
                    "transit_time": c["metrics"]["avg_transit_days"],
                    "shipment_count": c["metrics"]["shipments"],
                    "avg_cost": c["metrics"]["avg_cost"],
                    "delay_frequency": c["metrics"]["sla_violations"],
                    "delay_rate": round(100.0 - c["metrics"]["sla_compliance_pct"], 1),
                    "reliability_score": c["metrics"]["sla_compliance_pct"],
                    "efficiency_score": c["overall_health_score"],
                    "capacity_utilization": c["scores"]["hub_utilization_score"],
                    "partners": ["Swift LogiCo"]
                })

        sorted_by_eff = sorted(enriched_routes, key=lambda x: x.get("efficiency_score", 0), reverse=True) if enriched_routes else []
        top_efficient = sorted_by_eff[:10]
        top_inefficient = sorted_by_eff[-10:][::-1]
        most_delayed = sorted(enriched_routes, key=lambda x: x.get("delay_frequency", 0), reverse=True)[:10] if enriched_routes else []
        highest_cost = sorted(enriched_routes, key=lambda x: x.get("avg_cost", 0), reverse=True)[:10] if enriched_routes else []

        health_score = decision_payload.get("network_health_index", 85.0)

        # Merge decision engine recommendations and bottlenecks
        recommendations = decision_payload.get("recommendation_cards", [])
        bottlenecks = decision_payload.get("bottlenecks", [])

        return {
            "corridors": enriched_routes,
            "network_health_score": health_score,
            "top_efficient": top_efficient,
            "top_inefficient": top_inefficient,
            "most_delayed": most_delayed,
            "highest_cost": highest_cost,
            "recommendations": recommendations,
            "bottlenecks": bottlenecks,

            # Phase 53 AI Decision Engine Additions
            "decision_engine": decision_payload,
            "recommendation_cards": decision_payload.get("recommendation_cards", []),
            "alternative_routes": decision_payload.get("alternative_routes", []),
            "historical_patterns": decision_payload.get("historical_patterns", {}),
            "predictions": decision_payload.get("predictions", {}),
            "executive_ai_insights": decision_payload.get("executive_ai_insights", [])
        }

