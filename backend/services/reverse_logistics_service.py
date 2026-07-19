"""Reverse Logistics Service — Orchestrates returned shipment auditing, refurbishment queues, and recycling paths."""

from typing import Dict, Any, List
import pandas as pd

from backend.services.repository import repository
from backend.analytics.reverse_metrics import ReverseMetrics
from backend.utils.logger import logger

class ReverseLogisticsService:
    """Service providing returns audits, recovery statistics, and AI recommendations."""

    @classmethod
    def get_reverse_logistics(cls, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Compiles returns metrics, routes details, and refurbishment capacity suggestions.
        
        Args:
            filters: Global filters dictionary.
            
        Returns:
            Dict containing detailed reverse logistics payload.
        """
        logger.info("ReverseLogisticsService: Fetching reverse logistics intelligence payload.")

        # 1. Fetch baseline transactions
        df_tx = repository._processed_sheets.get("Logistics_Transactions")
        if df_tx is None or df_tx.empty:
            df_tx = pd.DataFrame()

        # 2. Compile simulated return transactions
        returns_list = ReverseMetrics.compile_returns(df_tx)

        # 3. Calculate return analytics
        analytics = ReverseMetrics.calculate_analytics(returns_list, len(df_tx))

        # 4. Generate AI recommendations (data-driven)
        recommendations = []
        if analytics["return_rate"] > 15.0:
            recommendations.append({
                "title": "High Return Rate Warning",
                "recommendation": "Return rate has surpassed the 15% threshold. Conduct product quality checks on parts showing frequent defects.",
                "benefit": "Lowers operational return costs by minimizing defect rates at supplier origin."
            })

        # Refurbish recommendation
        recommendations.append({
            "title": "Asset Refurbishment Routing",
            "recommendation": "Send damaged mechanical parts to nearest refurbishment center (Austin Hub) instead of regional scrap yards.",
            "benefit": f"Recovers up to $85.00 value per refurbished part. Total value: {analytics['recovered_value']} recovered."
        })

        # Merge returns recommendation
        recommendations.append({
            "title": "Returns Package Merger",
            "recommendation": "Consolidate individual customer returns at Hub-B before shipping to primary testing warehouses.",
            "benefit": "Saves 25% on reverse logistics transportation fees by leveraging full truckload (FTL) delivery."
        })

        # Recycling recommendation
        recommendations.append({
            "title": "Green Fleet Recycling",
            "recommendation": "Route scrap parts to certified recycling center (Houston TPR) to meet carbon neutrality credits.",
            "benefit": "Adds sustainability credits and reduces landfill tax costs."
        })

        return {
            "returns": returns_list,
            "analytics": analytics,
            "recommendations": recommendations,
            "summary": {
                "today_returns": len([r for r in returns_list if r["status"] == "Pending"]),
                "pending_returns": len([r for r in returns_list if r["status"] in ["Pending", "In Transit"]]),
                "refurbishment_queue": len([r for r in returns_list if r["status"] == "Processing"]),
                "recycling_volume": len([r for r in returns_list if r["status"] == "Recycled"])
            }
        }
