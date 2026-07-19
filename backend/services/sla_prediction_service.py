"""SLA Prediction Service — Orchestrates risk scoring across shipments, hubs, and corridors."""

from typing import Dict, Any
import pandas as pd

from backend.services.repository import repository
from backend.analytics.risk_engine import (
    score_shipment, score_hubs, score_corridors,
    generate_alerts, generate_recommendations
)
from backend.analytics.prediction_metrics import compile_summary, build_charts
from backend.utils.logger import logger


class SLAPredictionService:
    """Main service providing SLA breach predictions and risk forecasts."""

    @classmethod
    def get_prediction_payload(cls, filters: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("SLAPredictionService: Building SLA breach prediction payload.")

        df = repository._processed_sheets.get("Logistics_Transactions")
        if df is None or df.empty:
            df = pd.DataFrame()

        if not df.empty:
            avg_cost = float(df["Shipment_Cost"].mean())
            avg_dist = float(df["Route_Distance"].mean())

            # Score every shipment
            shipments = [score_shipment(row, avg_cost, avg_dist) for _, row in df.iterrows()]

            # Score hubs and corridors
            hubs       = score_hubs(df)
            corridors  = score_corridors(df)
        else:
            shipments, hubs, corridors = [], [], []
            avg_cost = avg_dist = 0.0

        # Aggregate summary KPIs
        summary = compile_summary(shipments, hubs, corridors)

        # Build Plotly chart payloads
        charts = build_charts(shipments, hubs)

        # Proactive alerts
        alerts = generate_alerts(shipments, hubs)

        # AI recommendations
        recommendations = generate_recommendations(shipments, hubs, corridors)

        return {
            "shipments":       shipments,
            "hubs":            hubs,
            "corridors":       corridors,
            "summary":         summary,
            "charts":          charts,
            "alerts":          alerts,
            "recommendations": recommendations
        }
