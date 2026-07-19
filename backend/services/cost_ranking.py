"""Ranking generator for logistics cost comparisons across routes, partners, and hubs."""

import pandas as pd
from typing import Dict, List, Any

from backend.models.cost_metrics import CostRankingEntry, CostRankings
from backend.utils.logger import logger


class CostRanking:
    """Generates sorted cost rankings for key logistics entities.
    
    Designed as a stateless service with class-level methods for reusability.
    """

    @classmethod
    def generate_rankings(cls, df: pd.DataFrame, top_n: int = 5) -> CostRankings:
        """Generates top/bottom cost rankings for routes, partners, and hubs.
        
        Args:
            df: Enriched transactions DataFrame with Origin_Hub, Destination_Hub,
                Logistics_Partner, and Shipment_Cost columns.
            top_n: Number of entries per ranking list.
            
        Returns:
            CostRankings containing 6 ranked lists.
        """
        logger.info(f"CostRanking: Generating rankings (top_n={top_n}).")

        if df is None or len(df) == 0 or "Shipment_Cost" not in df.columns:
            logger.warning("CostRanking: Insufficient data for rankings. Returning empty.")
            return CostRankings()

        rankings = CostRankings()

        # --- Route Rankings ---
        if "Origin_Hub" in df.columns and "Destination_Hub" in df.columns:
            df_routes = df.copy()
            df_routes["Route_Key"] = df_routes["Origin_Hub"] + " → " + df_routes["Destination_Hub"]
            route_costs = df_routes.groupby("Route_Key")["Shipment_Cost"].mean().reset_index()
            route_costs.columns = ["Route_Key", "avg_cost"]

            # Top Expensive Routes
            top_routes = route_costs.nlargest(top_n, "avg_cost")
            rankings.top_expensive_routes = [
                CostRankingEntry(rank=i + 1, entity_name=row["Route_Key"], metric_value=round(row["avg_cost"], 2))
                for i, row in top_routes.iterrows() if pd.notna(row["avg_cost"])
            ]
            # Re-index ranks
            for i, entry in enumerate(rankings.top_expensive_routes):
                entry.rank = i + 1

            # Lowest Cost Routes
            bottom_routes = route_costs.nsmallest(top_n, "avg_cost")
            rankings.lowest_cost_routes = [
                CostRankingEntry(rank=i + 1, entity_name=row["Route_Key"], metric_value=round(row["avg_cost"], 2))
                for i, row in bottom_routes.iterrows() if pd.notna(row["avg_cost"])
            ]
            for i, entry in enumerate(rankings.lowest_cost_routes):
                entry.rank = i + 1

        # --- Partner Rankings ---
        if "Logistics_Partner" in df.columns:
            partner_costs = df.groupby("Logistics_Partner")["Shipment_Cost"].mean().reset_index()
            partner_costs.columns = ["Partner", "avg_cost"]

            top_partners = partner_costs.nlargest(top_n, "avg_cost")
            rankings.highest_cost_partners = [
                CostRankingEntry(rank=i + 1, entity_name=row["Partner"], metric_value=round(row["avg_cost"], 2))
                for i, row in top_partners.iterrows() if pd.notna(row["avg_cost"])
            ]
            for i, entry in enumerate(rankings.highest_cost_partners):
                entry.rank = i + 1

            bottom_partners = partner_costs.nsmallest(top_n, "avg_cost")
            rankings.lowest_cost_partners = [
                CostRankingEntry(rank=i + 1, entity_name=row["Partner"], metric_value=round(row["avg_cost"], 2))
                for i, row in bottom_partners.iterrows() if pd.notna(row["avg_cost"])
            ]
            for i, entry in enumerate(rankings.lowest_cost_partners):
                entry.rank = i + 1

        # --- Hub Rankings ---
        if "Origin_Hub" in df.columns:
            hub_costs = df.groupby("Origin_Hub")["Shipment_Cost"].mean().reset_index()
            hub_costs.columns = ["Hub", "avg_cost"]

            top_hubs = hub_costs.nlargest(top_n, "avg_cost")
            rankings.highest_cost_hubs = [
                CostRankingEntry(rank=i + 1, entity_name=row["Hub"], metric_value=round(row["avg_cost"], 2))
                for i, row in top_hubs.iterrows() if pd.notna(row["avg_cost"])
            ]
            for i, entry in enumerate(rankings.highest_cost_hubs):
                entry.rank = i + 1

            bottom_hubs = hub_costs.nsmallest(top_n, "avg_cost")
            rankings.lowest_cost_hubs = [
                CostRankingEntry(rank=i + 1, entity_name=row["Hub"], metric_value=round(row["avg_cost"], 2))
                for i, row in bottom_hubs.iterrows() if pd.notna(row["avg_cost"])
            ]
            for i, entry in enumerate(rankings.lowest_cost_hubs):
                entry.rank = i + 1

        logger.info("CostRanking: Rankings Generated event logged.")
        return rankings
