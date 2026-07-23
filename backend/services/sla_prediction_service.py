from typing import Dict, Any, List
import pandas as pd
from backend.services.repository import repository
from backend.services.bi_service import BIService
from backend.analytics.risk_engine import score_shipment, score_hubs, score_corridors, generate_alerts, generate_recommendations
from backend.analytics.prediction_metrics import compile_summary, build_charts
from backend.services.sla_prediction_engine import SLAPredictionEngine
from backend.utils.logger import logger

class SLAPredictionService:
    """Main service providing SLA breach predictions and risk forecasts."""

    @classmethod
    def get_prediction_payload(cls, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Builds full SLA prediction payload including scored shipments, hubs, corridors, summary, charts, alerts, recommendations.
        
        Args:
            filters: Global filters dictionary.
            
        Returns:
            Dict containing detailed SLA prediction and risk intelligence payload.
        """
        logger.info("SLAPredictionService: Building SLA breach prediction payload.")

        df_tx = repository._processed_sheets.get("Logistics_Transactions")
        if df_tx is None or df_tx.empty:
            df_filtered = pd.DataFrame()
        else:
            df_filtered = BIService.apply_filters(df_tx, filters)

        if df_filtered.empty:
            shipments, hubs, corridors = [], [], []
        else:
            avg_cost = float(df_filtered["Shipment_Cost"].mean()) if "Shipment_Cost" in df_filtered.columns else 1000.0
            avg_dist = float(df_filtered["Route_Distance"].mean()) if "Route_Distance" in df_filtered.columns else 500.0
            
            shipments = [score_shipment(row, avg_cost, avg_dist) for _, row in df_filtered.iterrows()]
            hubs = score_hubs(df_filtered)
            corridors = score_corridors(df_filtered)

        summary = compile_summary(shipments, hubs, corridors)
        charts = build_charts(shipments, hubs)
        alerts = generate_alerts(shipments, hubs)
        recommendations = generate_recommendations(shipments, hubs, corridors)

        # Include node coordinates for Leaflet heatmap
        node_coords = {
            "HUB-DEL": [28.6139, 77.2090],
            "HUB-MUM": [19.0760, 72.8777],
            "HUB-BLR": [12.9716, 77.5946],
            "HUB-CHE": [13.0827, 80.2707],
            "HUB-HYD": [17.3850, 78.4867],
            "HUB-KOL": [22.5726, 88.3639],
            "HUB-PUN": [18.5204, 73.8567],
            "HUB-SIN": [1.3521, 103.8198]
        }

        # Include model evaluation and risk engine platform metrics
        ml_platform = SLAPredictionEngine.evaluate_sla_prediction_platform(filters)

        return {
            "status": "success",
            "shipments": shipments,
            "hubs": hubs,
            "corridors": corridors,
            "summary": summary,
            "charts": charts,
            "alerts": alerts,
            "recommendations": recommendations,
            "node_coordinates": node_coords,
            "ml_platform": ml_platform
        }
