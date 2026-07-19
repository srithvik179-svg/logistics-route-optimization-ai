"""Transit time ranking generator for routes, hubs, repair centers, and logistics partners."""

import pandas as pd
from typing import List

from backend.models.transit_metrics import TransitRankingEntry, TransitRankings
from backend.utils.logger import logger


class TransitRankingService:
    """Generates sorted transit time rankings for key logistics entities.

    Stateless service with class-level methods for reusability.
    """

    @classmethod
    def generate_rankings(cls, df: pd.DataFrame, transit_col: str = "Transit_Days", top_n: int = 5) -> TransitRankings:
        """Generates fastest/slowest rankings for routes, hubs, RCs, and partners.

        Args:
            df: Enriched transactions DataFrame with transit_col, Origin_Hub,
                Destination_Hub, Logistics_Partner, TPR_ID columns.
            transit_col: Column name containing transit time in days.
            top_n: Number of entries per ranking list.

        Returns:
            TransitRankings containing 8 ranked lists.
        """
        logger.info(f"TransitRankingService: Generating transit rankings (top_n={top_n}).")

        if df is None or len(df) == 0 or transit_col not in df.columns:
            logger.warning("TransitRankingService: Insufficient data. Returning empty rankings.")
            return TransitRankings()

        rankings = TransitRankings()

        # --- Route Rankings ---
        if "Origin_Hub" in df.columns and "Destination_Hub" in df.columns:
            df_r = df.copy()
            df_r["Route_Key"] = df_r["Origin_Hub"] + " → " + df_r["Destination_Hub"]
            route_agg = df_r.groupby("Route_Key").agg(
                avg_transit=(transit_col, "mean"),
                count=(transit_col, "count"),
            ).reset_index()

            rankings.fastest_routes = cls._rank(route_agg, "Route_Key", "avg_transit", "count", top_n, ascending=True)
            rankings.slowest_routes = cls._rank(route_agg, "Route_Key", "avg_transit", "count", top_n, ascending=False)

        # --- Hub Rankings (Origin) ---
        if "Origin_Hub" in df.columns:
            hub_agg = df.groupby("Origin_Hub").agg(
                avg_transit=(transit_col, "mean"),
                count=(transit_col, "count"),
            ).reset_index()

            rankings.fastest_hubs = cls._rank(hub_agg, "Origin_Hub", "avg_transit", "count", top_n, ascending=True)
            rankings.slowest_hubs = cls._rank(hub_agg, "Origin_Hub", "avg_transit", "count", top_n, ascending=False)

        # --- Repair Center Rankings ---
        if "TPR_ID" in df.columns:
            rc_agg = df.groupby("TPR_ID").agg(
                avg_transit=(transit_col, "mean"),
                count=(transit_col, "count"),
            ).reset_index()

            rankings.fastest_repair_centers = cls._rank(rc_agg, "TPR_ID", "avg_transit", "count", top_n, ascending=True)
            rankings.slowest_repair_centers = cls._rank(rc_agg, "TPR_ID", "avg_transit", "count", top_n, ascending=False)

        # --- Partner Rankings ---
        if "Logistics_Partner" in df.columns:
            partner_agg = df.groupby("Logistics_Partner").agg(
                avg_transit=(transit_col, "mean"),
                count=(transit_col, "count"),
            ).reset_index()

            rankings.fastest_partners = cls._rank(partner_agg, "Logistics_Partner", "avg_transit", "count", top_n, ascending=True)
            rankings.slowest_partners = cls._rank(partner_agg, "Logistics_Partner", "avg_transit", "count", top_n, ascending=False)

        logger.info("TransitRankingService: Transit Rankings Generated event logged.")
        return rankings

    @classmethod
    def _rank(
        cls,
        agg_df: pd.DataFrame,
        name_col: str,
        metric_col: str,
        count_col: str,
        top_n: int,
        ascending: bool,
    ) -> List[TransitRankingEntry]:
        """Helper to sort and build a ranking list."""
        sorted_df = agg_df.sort_values(metric_col, ascending=ascending).head(top_n)
        entries: List[TransitRankingEntry] = []
        for i, (_, row) in enumerate(sorted_df.iterrows()):
            entries.append(TransitRankingEntry(
                rank=i + 1,
                entity_name=str(row[name_col]),
                avg_transit_time=round(float(row[metric_col]), 2),
                shipment_count=int(row[count_col]),
            ))
        return entries
