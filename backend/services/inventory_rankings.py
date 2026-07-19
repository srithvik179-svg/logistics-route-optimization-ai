"""Ranking generator for logistics inventory comparisons."""

import pandas as pd
from typing import List, Dict, Any
from backend.models.inventory_metrics import RankingEntry, InventoryRankings
from backend.utils.logger import logger


class InventoryRankingService:
    """Generates inventory rankings for hubs, repair centers, and parts.

    Stateless service with class-level methods for reusability.
    """

    @classmethod
    def generate_rankings(
        cls,
        stock_df: pd.DataFrame,
        tx_df: pd.DataFrame,
        hub_master: pd.DataFrame,
        tpr_master: pd.DataFrame,
        top_n: int = 5
    ) -> InventoryRankings:
        """Generates inventory rankings.

        Args:
            stock_df: DataFrame with 'location', 'part_number', 'stock_level'.
            tx_df: Transactions DataFrame.
            hub_master: Hub Location Master DataFrame.
            tpr_master: Repair Center (TPR) Master DataFrame.
            top_n: Number of entries per ranking list.

        Returns:
            InventoryRankings containing sorted ranked entities.
        """
        logger.info(f"InventoryRankingService: Generating rankings (top_n={top_n}).")

        if stock_df is None or len(stock_df) == 0:
            logger.warning("InventoryRankingService: Empty stock levels. Returning empty rankings.")
            return InventoryRankings()

        rankings = InventoryRankings()

        hubs = hub_master["Hub_ID"].unique() if len(hub_master) > 0 else []
        rcs = tpr_master["TPR_ID"].unique() if len(tpr_master) > 0 else []

        # Aggregate current stock level by location
        loc_stock = stock_df.groupby("location")["stock_level"].sum().reset_index()
        loc_stock.columns = ["location", "total_stock"]

        # 1. Hub Rankings
        hub_stock = loc_stock[
            loc_stock["location"].isin(hubs) | loc_stock["location"].str.upper().str.startswith("HUB")
        ].copy()
        
        if len(hub_stock) > 0:
            top_h = hub_stock.nlargest(top_n, "total_stock")
            rankings.top_inventory_hubs = [
                RankingEntry(rank=i + 1, name=str(row["location"]), value=round(float(row["total_stock"]), 2))
                for i, row in top_h.reset_index().iterrows()
            ]

            low_h = hub_stock.nsmallest(top_n, "total_stock")
            rankings.lowest_inventory_hubs = [
                RankingEntry(rank=i + 1, name=str(row["location"]), value=round(float(row["total_stock"]), 2))
                for i, row in low_h.reset_index().iterrows()
            ]

        # 2. Repair Center Rankings
        rc_stock = loc_stock[
            loc_stock["location"].isin(rcs) | ~loc_stock["location"].isin(hubs) & ~loc_stock["location"].str.upper().str.startswith("HUB")
        ].copy()

        if len(rc_stock) > 0:
            top_rc = rc_stock.nlargest(top_n, "total_stock")
            rankings.top_repair_centers = [
                RankingEntry(rank=i + 1, name=str(row["location"]), value=round(float(row["total_stock"]), 2))
                for i, row in top_rc.reset_index().iterrows()
            ]

        # 3. Top Moving Parts (based on shipment transaction counts)
        if tx_df is not None and len(tx_df) > 0 and "Part_Number" in tx_df.columns:
            part_freq = tx_df.groupby("Part_Number")["Quantity"].sum().reset_index()
            part_freq.columns = ["Part_Number", "total_qty"]

            top_p = part_freq.nlargest(top_n, "total_qty")
            rankings.top_moving_parts = [
                RankingEntry(rank=i + 1, name=str(row["Part_Number"]), value=round(float(row["total_qty"]), 2))
                for i, row in top_p.reset_index().iterrows()
            ]

            bottom_p = part_freq.nsmallest(top_n, "total_qty")
            rankings.slowest_moving_parts = [
                RankingEntry(rank=i + 1, name=str(row["Part_Number"]), value=round(float(row["total_qty"]), 2))
                for i, row in bottom_p.reset_index().iterrows()
            ]

        logger.info("InventoryRankingService: Inventory Rankings Generated.")
        return rankings
