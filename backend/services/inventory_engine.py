"""Inventory Analytics Engine — Orchestrator with in-memory caching.

Primary entry point for all inventory analytics operations. It fetches master
and transaction data from the Repository Layer, simulates stock positions,
calculates overview metrics, and delegates to specialised sub-services.
"""

import json
import pandas as pd
from typing import Dict, Any, List, Tuple
from datetime import datetime

from backend.services.repository import repository
from backend.services.geospatial_service import GeospatialService
from backend.services.inventory_statistics import InventoryStatistics
from backend.services.inventory_rankings import InventoryRankingService
from backend.services.inventory_outliers import InventoryOutlierDetector
from backend.services.inventory_trends import InventoryTrendsService
from backend.models.inventory_metrics import (
    InventoryAnalyticsPayload,
    InventoryOverviewMetrics,
    InventoryMovement,
    InventoryMovementDimension,
    StockAnalysis,
    StockLevelItem,
    UtilizationAnalysis,
    InventoryRankings,
    InventoryOutliers,
    InventoryTrends,
)
from backend.utils.logger import logger


class InventoryEngine:
    """Orchestrates inventory analytics across the logistics network.

    Responsibilities:
        1. Loads processed sheets from the Repository Layer.
        2. Simulates stock level positions (initial baseline = 100 per node-part).
        3. Tracks incoming (+) and outgoing (-) transactions.
        4. Calculates overview KPIs and movements.
        5. Delegates stock classification, utilization, rankings, outliers, and trends.
        6. Caches results using filter keys.
    """

    _cache: Dict[str, InventoryAnalyticsPayload] = {}

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the in-memory cache."""
        cls._cache.clear()
        logger.info("InventoryEngine: Cache cleared.")

    @classmethod
    def get_inventory_payload(cls, filters: Dict[str, Any]) -> InventoryAnalyticsPayload:
        """Main entry point returning a fully computed InventoryAnalyticsPayload.

        Args:
            filters: Global filters dictionary.

        Returns:
            InventoryAnalyticsPayload containing comprehensive inventory analytics.
        """
        logger.info(f"InventoryEngine: Inventory Engine Started. Filters: {filters}")

        # --- Cache Lookup ---
        cache_key = cls._build_cache_key(filters)
        if cache_key in cls._cache:
            logger.info("InventoryEngine: Cache HIT — returning cached payload.")
            cached = cls._cache[cache_key]
            cached.cached = True
            return cached

        # --- Load sheets ---
        df_tx_raw = repository._processed_sheets.get("Logistics_Transactions")
        df_hub = repository._processed_sheets.get("Hub_Location_Master")
        tpr_sheet_name = "TPR_Master" if repository.sheet_exists("TPR_Master") else "Repair_Center_Master"
        df_tpr = repository._processed_sheets.get(tpr_sheet_name)
        df_parts = repository._processed_sheets.get("Parts_Master")

        # Fallbacks
        if df_tx_raw is None or len(df_tx_raw) == 0:
            df_tx_raw = pd.DataFrame()
        if df_hub is None or len(df_hub) == 0:
            df_hub = pd.DataFrame(columns=["Hub_ID", "Hub_Name", "Latitude", "Longitude", "City", "Region"])
        if df_tpr is None or len(df_tpr) == 0:
            df_tpr = pd.DataFrame(columns=["TPR_ID", "TPR_Name", "Coverage_Region", "SLA_Compliance_Target", "Rating"])
        if df_parts is None or len(df_parts) == 0:
            df_parts = pd.DataFrame(columns=["Part_Number", "Part_Name", "Category", "Weight_Kg", "Dimensions_Cm3"])

        # Enriched fields
        df_tx = cls._enrich_transactions(df_tx_raw, df_tpr)

        # Apply global filters
        df_filtered = GeospatialService._apply_geospatial_filters(df_tx, df_parts, filters)

        if len(df_filtered) == 0:
            logger.warning("InventoryEngine: Empty dataset after filtering.")
            empty = cls._empty_payload(filters)
            cls._cache[cache_key] = empty
            return empty

        # --- Simulate Inventory Stock Positions ---
        stock_df, stock_history = cls._simulate_stock_levels(df_filtered, df_hub, df_tpr, df_parts)

        # --- 1. Overview Metrics (delegated) ---
        overview = InventoryStatistics.compute_overview(stock_df, df_hub, df_tpr, df_parts)
        logger.info("InventoryEngine: Inventory Metrics Generated.")

        # --- 2. Inventory Movement ---
        movement = cls._calculate_movement(df_filtered, df_hub, df_tpr)

        # --- 3. Stock Level Classification & Fast/Slow Parts ---
        stock_analysis = cls._perform_stock_analysis(stock_df, df_filtered)

        # --- 4. Node capacities and utilization rate ---
        capacities = cls._get_capacities(df_hub, df_tpr)
        utilization = cls._calculate_utilization(stock_df, df_filtered, capacities)

        # --- 5. Rankings (delegated) ---
        rankings = InventoryRankingService.generate_rankings(stock_df, df_filtered, df_hub, df_tpr, top_n=5)
        logger.info("InventoryEngine: Inventory Rankings Generated.")

        # --- 6. Outliers & Anomalies (delegated) ---
        outliers = InventoryOutlierDetector.detect_anomalies(stock_df, df_filtered, capacities)
        logger.info("InventoryEngine: Inventory Outliers Generated.")

        # --- 7. Trends (delegated) ---
        trends = InventoryTrendsService.generate_trends(df_filtered, stock_history)
        logger.info("InventoryEngine: Inventory Trends Generated.")

        payload = InventoryAnalyticsPayload(
            overview=overview,
            movement=movement,
            stock_analysis=stock_analysis,
            utilization=utilization,
            rankings=rankings,
            outliers=outliers,
            trends=trends,
            filters_applied=filters,
            cached=False
        )

        # Cache payload
        cls._cache[cache_key] = payload
        return payload

    # ────────────────────────────────────────────
    # Private Helpers
    # ────────────────────────────────────────────

    @classmethod
    def _build_cache_key(cls, filters: Dict[str, Any]) -> str:
        sorted_items = sorted(
            ((k, v) for k, v in filters.items() if v),
            key=lambda x: x[0]
        )
        return json.dumps(sorted_items, default=str)

    @classmethod
    def _enrich_transactions(cls, df: pd.DataFrame, df_tpr: pd.DataFrame) -> pd.DataFrame:
        """Enriches the transaction dataset with partners, priorities, and flow types."""
        if len(df) == 0:
            return df
        
        df_enriched = df.copy()

        tpr_names = (
            list(df_tpr["TPR_Name"])
            if len(df_tpr) > 0 and "TPR_Name" in df_tpr.columns
            else ["Swift LogiCo", "Apex Freight", "LoneStar Delivery"]
        )
        df_enriched["Logistics_Partner"] = [tpr_names[i % len(tpr_names)] for i in range(len(df))]
        df_enriched["TPR_ID"] = df_enriched["Logistics_Partner"].map(GeospatialService.TPR_NAME_TO_ID).fillna("TPR-001")

        priorities = []
        flow_types = []
        for _, row in df_enriched.iterrows():
            dest = str(row.get("Destination_Hub", ""))
            dist = float(row.get("Route_Distance") or 0.0)
            cost = float(row.get("Shipment_Cost") or 0.0)

            if dest.upper().startswith("TPR"):
                flow_types.append("Outbound to TPR")
            elif dest.upper().startswith("HUB"):
                flow_types.append("Hub-to-Hub Transfer")
            else:
                flow_types.append("Outbound to TPR")

            if dist > 300.0 or cost > 300.0:
                priorities.append("High Priority")
            elif dist > 100.0 or cost > 100.0:
                priorities.append("Medium Priority")
            else:
                priorities.append("Low Priority")

        df_enriched["Priority"] = priorities
        df_enriched["Flow_Type"] = flow_types

        return df_enriched

    @classmethod
    def _simulate_stock_levels(
        cls,
        tx_df: pd.DataFrame,
        hub_df: pd.DataFrame,
        tpr_df: pd.DataFrame,
        parts_df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """Simulates inventory stock levels per location and part number over time."""
        hubs = list(hub_df["Hub_ID"].unique()) if len(hub_df) > 0 else ["HUB-001", "HUB-002", "HUB-003", "HUB-004", "HUB-005"]
        rcs = list(tpr_df["TPR_ID"].unique()) if len(tpr_df) > 0 else ["TPR-001", "TPR-002", "TPR-003"]
        locations = hubs + rcs

        parts = list(parts_df["Part_Number"].unique()) if len(parts_df) > 0 else ["PART-001", "PART-002", "PART-003"]

        # Initialize stock dictionary
        # Combination of location and part_number starts with 100.0 units
        stock_matrix: Dict[Tuple[str, str], float] = {
            (loc, part): 100.0 for loc in locations for part in parts
        }

        # Chronological stock state history
        history: List[Dict[str, Any]] = []

        if len(tx_df) > 0 and "Order_Date" in tx_df.columns:
            work_df = tx_df.copy()
            work_df["Order_Date"] = pd.to_datetime(work_df["Order_Date"])
            work_df = work_df.sort_values("Order_Date")

            # Group transactions by day to record daily stock state
            for date_day, day_group in work_df.groupby(work_df["Order_Date"].dt.date):
                for _, row in day_group.iterrows():
                    part = str(row.get("Part_Number"))
                    qty = float(row.get("Quantity") or 0.0)
                    origin = str(row.get("Origin_Hub"))
                    dest = str(row.get("Destination_Hub"))

                    # Decrement origin stock
                    orig_key = (origin, part)
                    if orig_key in stock_matrix:
                        stock_matrix[orig_key] = max(0.0, stock_matrix[orig_key] - qty)

                    # Increment destination stock
                    dest_key = (dest, part)
                    if dest_key in stock_matrix:
                        stock_matrix[dest_key] = stock_matrix[dest_key] + qty

                # Record daily average stock level
                avg_stock = sum(stock_matrix.values()) / len(stock_matrix)
                history.append({
                    "date": datetime.combine(date_day, datetime.min.time()),
                    "avg_stock": avg_stock
                })
        else:
            # No transactions, standard baseline state
            history.append({
                "date": datetime.now(),
                "avg_stock": 100.0
            })

        # Assemble final stock DataFrame
        records = []
        for (loc, part), stock in stock_matrix.items():
            records.append({
                "location": loc,
                "part_number": part,
                "stock_level": stock
            })

        return pd.DataFrame(records), history

    @classmethod
    def _calculate_movement(
        cls,
        tx_df: pd.DataFrame,
        hub_df: pd.DataFrame,
        tpr_df: pd.DataFrame
    ) -> InventoryMovement:
        """Generates outgoing, incoming, and net movement datasets."""
        total_in = float(tx_df["Quantity"].sum())
        total_out = total_in  # Flows are balanced globally in transaction records

        # Helper to compute movement per group dimension
        def _get_movement_map(groupby_col: str) -> Dict[str, InventoryMovementDimension]:
            result_map = {}
            if groupby_col not in tx_df.columns:
                return result_map

            # Incoming to destination
            inc_grp = tx_df.groupby(groupby_col)["Quantity"].sum()
            for name, val in inc_grp.items():
                name_str = str(name)
                result_map[name_str] = InventoryMovementDimension(
                    incoming=round(float(val), 2),
                    outgoing=0.0,
                    net_movement=round(float(val), 2)
                )

            # Outgoing from origin
            out_grp = tx_df.groupby(groupby_col)["Quantity"].sum()
            for name, val in out_grp.items():
                name_str = str(name)
                dim = result_map.get(name_str)
                if dim:
                    dim.outgoing = round(float(val), 2)
                    dim.net_movement = round(dim.incoming - dim.outgoing, 2)
                else:
                    result_map[name_str] = InventoryMovementDimension(
                        incoming=0.0,
                        outgoing=round(float(val), 2),
                        net_movement=round(-float(val), 2)
                    )
            return result_map

        # Movement per hub
        by_hub_map = {}
        hubs = list(hub_df["Hub_ID"].unique()) if len(hub_df) > 0 else []
        for loc in hubs:
            incoming = float(tx_df[tx_df["Destination_Hub"] == loc]["Quantity"].sum())
            outgoing = float(tx_df[tx_df["Origin_Hub"] == loc]["Quantity"].sum())
            by_hub_map[loc] = InventoryMovementDimension(
                incoming=round(incoming, 2),
                outgoing=round(outgoing, 2),
                net_movement=round(incoming - outgoing, 2)
            )

        # Region movement map
        hub_reg = {}
        if len(hub_df) > 0 and "Hub_ID" in hub_df.columns and "Region" in hub_df.columns:
            hub_reg = dict(zip(hub_df["Hub_ID"], hub_df["Region"]))

        tpr_reg = {}
        if len(tpr_df) > 0 and "TPR_ID" in tpr_df.columns and "Coverage_Region" in tpr_df.columns:
            tpr_reg = dict(zip(tpr_df["TPR_ID"], tpr_df["Coverage_Region"]))

        by_region_map: Dict[str, InventoryMovementDimension] = {}
        for _, row in tx_df.iterrows():
            qty = float(row["Quantity"] or 0.0)
            origin = str(row["Origin_Hub"])
            dest = str(row["Destination_Hub"])

            # Map origin/dest to region
            orig_reg = hub_reg.get(origin) or tpr_reg.get(origin) or "Unknown"
            dest_reg = hub_reg.get(dest) or tpr_reg.get(dest) or "Unknown"

            # Increment outgoing
            dim_orig = by_region_map.get(orig_reg, InventoryMovementDimension(incoming=0.0, outgoing=0.0, net_movement=0.0))
            dim_orig.outgoing += qty
            dim_orig.net_movement -= qty
            by_region_map[orig_reg] = dim_orig

            # Increment incoming
            dim_dest = by_region_map.get(dest_reg, InventoryMovementDimension(incoming=0.0, outgoing=0.0, net_movement=0.0))
            dim_dest.incoming += qty
            dim_dest.net_movement += qty
            by_region_map[dest_reg] = dim_dest

        # Round region maps
        for k, d in by_region_map.items():
            d.incoming = round(d.incoming, 2)
            d.outgoing = round(d.outgoing, 2)
            d.net_movement = round(d.incoming - d.outgoing, 2)

        # Movement per part
        by_part_map = _get_movement_map("Part_Number")

        # Movement per month & quarter
        by_month_map = _get_movement_map("Order_Date_Month")
        by_quarter_map = _get_movement_map("Order_Date_Quarter")

        return InventoryMovement(
            incoming_total=round(total_in, 2),
            outgoing_total=round(total_out, 2),
            by_hub=by_hub_map,
            by_region=by_region_map,
            by_part=by_part_map,
            by_month=by_month_map,
            by_quarter=by_quarter_map
        )

    @classmethod
    def _perform_stock_analysis(cls, stock_df: pd.DataFrame, tx_df: pd.DataFrame) -> StockAnalysis:
        """Classifies items by stock level categories and extracts fast/slow moving parts."""
        high_stock = []
        low_stock = []
        critical_stock = []
        zero_stock = []

        for _, row in stock_df.iterrows():
            loc = str(row["location"])
            part = str(row["part_number"])
            lvl = float(row["stock_level"])

            item = StockLevelItem(location=loc, part_number=part, stock_level=round(lvl, 2))

            if lvl > 120.0:
                high_stock.append(item)
            elif lvl == 0.0:
                zero_stock.append(item)
            elif 0.0 < lvl <= 10.0:
                critical_stock.append(item)
            elif 10.0 < lvl <= 50.0:
                low_stock.append(item)

        # Fast and Slow parts (based on sum of transaction Quantities)
        fast_parts = []
        slow_parts = []
        if len(tx_df) > 0 and "Part_Number" in tx_df.columns:
            part_sum = tx_df.groupby("Part_Number")["Quantity"].sum().sort_values(ascending=False)
            fast_parts = list(part_sum.head(3).index)
            slow_parts = list(part_sum.tail(3).index)

        return StockAnalysis(
            high_stock_items=high_stock,
            low_stock_items=low_stock,
            critical_stock_items=critical_stock,
            zero_stock_items=zero_stock,
            fast_moving_parts=fast_parts,
            slow_moving_parts=slow_parts
        )

    @classmethod
    def _get_capacities(cls, hub_df: pd.DataFrame, tpr_df: pd.DataFrame) -> Dict[str, float]:
        """Builds a mapping of location capacity thresholds."""
        capacities = {}

        # Hub capacities (retrieve from COORDINATES_FALLBACK if present, else default to 5000.0)
        if len(hub_df) > 0:
            for h in hub_df["Hub_ID"].unique():
                h_str = str(h)
                capacities[h_str] = GeospatialService.COORDINATES_FALLBACK.get(h_str, {}).get("capacity") or 5000.0

        # TPR capacities (retrieve from COORDINATES_FALLBACK if present, else default to 2000.0)
        if len(tpr_df) > 0:
            for rc in tpr_df["TPR_ID"].unique():
                rc_str = str(rc)
                capacities[rc_str] = GeospatialService.COORDINATES_FALLBACK.get(rc_str, {}).get("capacity") or 2000.0

        return capacities

    @classmethod
    def _calculate_utilization(
        cls,
        stock_df: pd.DataFrame,
        tx_df: pd.DataFrame,
        capacities: Dict[str, float]
    ) -> UtilizationAnalysis:
        """Calculates capacities utilization, occupancy, and turnover ratios."""
        # Sum stock level by location
        loc_stock = stock_df.groupby("location")["stock_level"].sum().reset_index()

        hub_utils = {}
        rc_utils = {}
        total_occupancy_stock = 0.0
        total_capacity = 0.0

        for _, row in loc_stock.iterrows():
            loc = str(row["location"])
            stock = float(row["stock_level"])
            cap = capacities.get(loc, 1000.0)
            
            util = round((stock / cap) * 100.0, 1) if cap > 0 else 0.0

            if loc.upper().startswith("HUB"):
                hub_utils[loc] = util
            else:
                rc_utils[loc] = util

            total_occupancy_stock += stock
            total_capacity += cap

        avg_cap = sum(capacities.values()) / len(capacities) if len(capacities) > 0 else 1000.0
        net_occupancy = (total_occupancy_stock / total_capacity) * 100.0 if total_capacity > 0 else 0.0

        # Turnover ratio = outgoing units / average inventory
        # Total outgoing is total quantity moved
        outgoing_units = float(tx_df["Quantity"].sum()) if len(tx_df) > 0 else 0.0
        avg_inv = total_occupancy_stock if total_occupancy_stock > 0 else 100.0
        turnover = outgoing_units / avg_inv

        return UtilizationAnalysis(
            hub_utilization=hub_utils,
            repair_center_utilization=rc_utils,
            avg_inventory_capacity=round(avg_cap, 2),
            inventory_occupancy=round(net_occupancy, 1),
            inventory_turnover_ratio=round(turnover, 2)
        )

    @classmethod
    def _empty_payload(cls, filters: Dict[str, Any]) -> InventoryAnalyticsPayload:
        return InventoryAnalyticsPayload(
            overview=InventoryOverviewMetrics(
                total_inventory=0.0, avg_inventory=0.0, min_inventory=0.0, max_inventory=0.0,
                inventory_variance=0.0, inventory_std_deviation=0.0,
                inventory_per_hub={}, inventory_per_repair_center={},
                inventory_per_part_category={}, inventory_per_region={}, inventory_per_partner={}
            ),
            movement=InventoryMovement(incoming_total=0.0, outgoing_total=0.0),
            stock_analysis=StockAnalysis(),
            utilization=UtilizationAnalysis(avg_inventory_capacity=1000.0, inventory_occupancy=0.0, inventory_turnover_ratio=0.0),
            rankings=InventoryRankings(),
            outliers=InventoryOutliers(),
            trends=InventoryTrends(),
            filters_applied=filters,
            cached=False
        )
