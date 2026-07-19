"""Stateless descriptive statistics calculator for inventory stock levels."""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from backend.utils.logger import logger
from backend.models.inventory_metrics import InventoryOverviewMetrics


class InventoryStatistics:
    """Computes descriptive statistical measures and dimensions for inventory stock levels.

    Stateless service designed for reusability and dependency injection.
    """

    @classmethod
    def compute_overview(
        cls,
        stock_df: pd.DataFrame,
        hub_master: pd.DataFrame,
        tpr_master: pd.DataFrame,
        parts_master: pd.DataFrame
    ) -> InventoryOverviewMetrics:
        """Calculates inventory statistics and dimensional aggregations.

        Args:
            stock_df: DataFrame containing 'location', 'part_number', and 'stock_level'.
            hub_master: Hub Master DataFrame.
            tpr_master: Repair Center (TPR) Master DataFrame.
            parts_master: Parts Master DataFrame.

        Returns:
            InventoryOverviewMetrics containing descriptive statistics and aggregated dimensions.
        """
        logger.info("InventoryStatistics: Computing inventory metrics.")

        if stock_df is None or len(stock_df) == 0:
            logger.warning("InventoryStatistics: Empty stock dataset. Returning zeroed metrics.")
            return cls._empty_overview()

        levels = stock_df["stock_level"].astype(float)
        total = float(levels.sum())
        avg = float(levels.mean())
        minimum = float(levels.min())
        maximum = float(levels.max())
        var = float(levels.var(ddof=1)) if len(levels) > 1 else 0.0
        std = float(levels.std(ddof=1)) if len(levels) > 1 else 0.0

        # --- Sub-dimensions maps ---
        hubs = hub_master["Hub_ID"].unique() if len(hub_master) > 0 else []
        rcs = tpr_master["TPR_ID"].unique() if len(tpr_master) > 0 else []

        by_hub: Dict[str, float] = {}
        by_rc: Dict[str, float] = {}
        for loc, group in stock_df.groupby("location"):
            loc_sum = round(float(group["stock_level"].sum()), 2)
            if loc in hubs:
                by_hub[loc] = loc_sum
            elif loc in rcs:
                by_rc[loc] = loc_sum
            else:
                # Classify based on string naming conventions
                if loc.upper().startswith("HUB"):
                    by_hub[loc] = loc_sum
                else:
                    by_rc[loc] = loc_sum

        # Aggregate per category
        by_cat: Dict[str, float] = {}
        if len(parts_master) > 0 and "Part_Number" in parts_master.columns and "Category" in parts_master.columns:
            m_df = stock_df.merge(parts_master[["Part_Number", "Category"]], left_on="part_number", right_on="Part_Number", how="left")
            for cat, group in m_df.groupby("Category"):
                by_cat[str(cat)] = round(float(group["stock_level"].sum()), 2)

        # Aggregate per region & partner
        by_region: Dict[str, float] = {}
        by_partner: Dict[str, float] = {}

        # Hub Region Map
        hub_regions = {}
        if len(hub_master) > 0 and "Hub_ID" in hub_master.columns and "Region" in hub_master.columns:
            hub_regions = dict(zip(hub_master["Hub_ID"], hub_master["Region"]))

        # TPR Region and Name Map
        tpr_regions = {}
        tpr_names = {}
        if len(tpr_master) > 0 and "TPR_ID" in tpr_master.columns:
            if "Coverage_Region" in tpr_master.columns:
                tpr_regions = dict(zip(tpr_master["TPR_ID"], tpr_master["Coverage_Region"]))
            if "TPR_Name" in tpr_master.columns:
                tpr_names = dict(zip(tpr_master["TPR_ID"], tpr_master["TPR_Name"]))

        for loc, group in stock_df.groupby("location"):
            loc_sum = float(group["stock_level"].sum())
            # Find region
            reg = "Unknown"
            if loc in hub_regions:
                reg = hub_regions[loc]
            elif loc in tpr_regions:
                reg = tpr_regions[loc]
            by_region[reg] = by_region.get(reg, 0.0) + loc_sum

            # Find partner (only for TPRs)
            if loc in tpr_names:
                p_name = tpr_names[loc]
                by_partner[p_name] = by_partner.get(p_name, 0.0) + loc_sum

        # Round maps values
        by_region = {k: round(v, 2) for k, v in by_region.items()}
        by_partner = {k: round(v, 2) for k, v in by_partner.items()}

        logger.info("InventoryStatistics: Inventory Metrics Generated.")

        return InventoryOverviewMetrics(
            total_inventory=round(total, 2),
            avg_inventory=round(avg, 2),
            min_inventory=round(minimum, 2),
            max_inventory=round(maximum, 2),
            inventory_variance=round(var, 2),
            inventory_std_deviation=round(std, 2),
            inventory_per_hub=by_hub,
            inventory_per_repair_center=by_rc,
            inventory_per_part_category=by_cat,
            inventory_per_region=by_region,
            inventory_per_partner=by_partner
        )

    @classmethod
    def _empty_overview(cls) -> InventoryOverviewMetrics:
        """Returns a zeroed overview payload."""
        return InventoryOverviewMetrics(
            total_inventory=0.0, avg_inventory=0.0, min_inventory=0.0, max_inventory=0.0,
            inventory_variance=0.0, inventory_std_deviation=0.0,
            inventory_per_hub={}, inventory_per_repair_center={},
            inventory_per_part_category={}, inventory_per_region={}, inventory_per_partner={}
        )
