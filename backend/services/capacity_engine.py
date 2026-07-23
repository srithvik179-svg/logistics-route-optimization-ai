"""Network Capacity Analytics Engine — Orchestrator with in-memory caching.

Primary entry point for network capacity analysis. Loads processed datasets,
simulates node-level capacities, computes utilization statistics, and delegates
to sub-services for breakdowns, rankings, bottlenecks, and trends.
"""

import json
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime

from backend.services.repository import repository
from backend.services.geospatial_service import GeospatialService
from backend.services.inventory_engine import InventoryEngine
from backend.services.capacity_statistics import CapacityStatistics
from backend.services.capacity_rankings import CapacityRankingService
from backend.services.capacity_bottlenecks import CapacityBottleneckDetector
from backend.services.capacity_trends import CapacityTrendsService
from backend.models.capacity_metrics import (
    CapacityAnalyticsPayload,
    CapacityOverviewMetrics,
    NodeCapacityMetrics,
    RegionalCapacityBreakdown,
    CapacityRankings,
    CapacityBottlenecks,
    CapacityTrends,
)
from backend.utils.logger import logger


class CapacityEngine:
    """Orchestrates network capacity analytics across all logistics resources.

    Responsibilities:
        1. Loads processed datasets from Repository.
        2. Simulates storage capacities and active loads.
        3. Computes node KPIs (throughput, utilization %, densities).
        4. Delegates to statistics, rankings, bottlenecks, and trends.
        5. Caches payloads keyed by filters.
    """

    _cache: Dict[str, CapacityAnalyticsPayload] = {}

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the in-memory cache."""
        cls._cache.clear()
        logger.info("CapacityEngine: Cache cleared.")

    @classmethod
    def get_capacity_analytics(cls, filters: Dict[str, Any]) -> CapacityAnalyticsPayload:
        """Main entry point returning a fully computed CapacityAnalyticsPayload.

        Args:
            filters: Global filters dictionary.

        Returns:
            CapacityAnalyticsPayload payload.
        """
        logger.info(f"CapacityEngine: Capacity Engine Started. Filters: {filters}")

        # --- Clear cache to ensure fresh calculations ---
        cls._cache.clear()

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
            logger.warning("CapacityEngine: Empty dataset after filtering.")
            empty = cls._empty_payload(filters)
            cls._cache[cache_key] = empty
            return empty

        # Get simulated stock positions to compute used capacity occupancy
        inventory_payload = InventoryEngine.get_inventory_payload(filters)
        stock_overview = inventory_payload.overview
        stock_hubs = stock_overview.inventory_per_hub
        stock_rcs = stock_overview.inventory_per_repair_center

        # Build location analysis lists
        hubs_list = []
        rcs_list = []

        # Hub capacities mapping
        hubs = list(df_hub["Hub_ID"].unique()) if len(df_hub) > 0 and "Hub_ID" in df_hub.columns else ["HUB-BLR", "HUB-DEL", "HUB-MUM", "HUB-CHE", "HUB-HYD", "HUB-PUN", "HUB-KOL", "HUB-AHM", "HUB-SIN", "HUB-KUL", "HUB-DXB", "HUB-AMS"]
        for h in hubs:
            cap = 5000.0
            util_pct = 50.0
            if len(df_hub) > 0 and "Hub_ID" in df_hub.columns:
                row = df_hub[df_hub["Hub_ID"] == h]
                if len(row) > 0:
                    cap = float(row.iloc[0].get("Inventory_Capacity") or 5000.0)
                    if "Utilisation_Pct" in row.columns and not pd.isna(row.iloc[0].get("Utilisation_Pct")):
                        u_val = float(row.iloc[0].get("Utilisation_Pct"))
                        util_pct = u_val * 100.0 if u_val <= 1.0 else u_val
            else:
                cap = GeospatialService.COORDINATES_FALLBACK.get(h, {}).get("capacity") or 5000.0

            util_pct = round(util_pct, 1)
            used = round(cap * (util_pct / 100.0), 2)

            # Node Workload (trans transactions count)
            node_txs = df_filtered[(df_filtered["Origin_Hub"] == h) | (df_filtered["Destination_Hub"] == h)]
            workload = len(node_txs)
            
            # Throughput
            throughput = float(node_txs["Quantity"].sum()) if len(node_txs) > 0 else 0.0

            hubs_list.append(NodeCapacityMetrics(
                node_id=h,
                capacity=cap,
                used_capacity=used,
                utilization_pct=util_pct,
                remaining_capacity=round(cap - used, 2),
                workload=workload,
                shipment_density=round(workload / cap, 4),
                inventory_density=round(used / cap, 4),
                throughput=round(throughput, 2)
            ))

        # Repair Center capacity mapping
        rcs = list(df_tpr["TPR_ID"].unique()) if len(df_tpr) > 0 and "TPR_ID" in df_tpr.columns else ["TPR-BLR-01", "TPR-BLR-02", "TPR-DEL-01", "TPR-MUM-01", "TPR-CHE-01", "TPR-HYD-01", "TPR-SIN-01", "TPR-KUL-01"]
        for rc in rcs:
            cap = 2000.0
            util_pct = 50.0
            if len(df_tpr) > 0 and "TPR_ID" in df_tpr.columns:
                row = df_tpr[df_tpr["TPR_ID"] == rc]
                if len(row) > 0:
                    cap = float(row.iloc[0].get("Repair_Capacity_Per_Day") or 2000.0)
                    wl = float(row.iloc[0].get("Current_Workload") or 0.0)
                    util_pct = (wl / cap) * 100.0 if cap > 0 else 50.0
            else:
                cap = GeospatialService.COORDINATES_FALLBACK.get(rc, {}).get("capacity") or 2000.0

            util_pct = round(util_pct, 1)
            used = round(cap * (util_pct / 100.0), 2)

            node_txs = df_filtered[(df_filtered["Origin_Hub"] == rc) | (df_filtered["Destination_Hub"] == rc)]
            workload = len(node_txs)
            throughput = float(node_txs["Quantity"].sum()) if len(node_txs) > 0 else 0.0

            rcs_list.append(NodeCapacityMetrics(
                node_id=rc,
                capacity=cap,
                used_capacity=used,
                utilization_pct=util_pct,
                remaining_capacity=round(cap - used, 2),
                workload=workload,
                shipment_density=round(workload / cap, 4),
                inventory_density=round(used / cap, 4),
                throughput=round(throughput, 2)
            ))

        # --- 1. Overview Metrics (delegated) ---
        overview = CapacityStatistics.compute_overview(hubs_list, rcs_list)
        logger.info("CapacityEngine: Capacity Metrics Generated.")

        # --- 2. Multi-dimensional regional capacity breakdowns (delegated) ---
        regional_analysis = CapacityStatistics.compute_regional_analysis(
            hubs_list + rcs_list, df_hub, df_tpr, df_filtered
        )

        # --- 3. Rankings (delegated) ---
        rankings = CapacityRankingService.generate_rankings(hubs_list, rcs_list, regional_analysis, top_n=5)
        logger.info("CapacityEngine: Capacity Rankings Generated.")

        # --- 4. Bottleneck & Anomalies (delegated) ---
        bottlenecks = CapacityBottleneckDetector.detect_bottlenecks(hubs_list, rcs_list)
        logger.info("CapacityEngine: Capacity Bottlenecks Generated.")

        # --- 5. Trends (delegated) ---
        total_cap_limit = sum(n.capacity for n in hubs_list + rcs_list)
        trends = CapacityTrendsService.generate_trends(df_filtered, total_cap_limit)
        logger.info("CapacityEngine: Capacity Trends Generated.")

        payload = CapacityAnalyticsPayload(
            overview=overview,
            hubs_analysis=hubs_list,
            repair_centers_analysis=rcs_list,
            regional_analysis=regional_analysis,
            bottlenecks=bottlenecks,
            rankings=rankings,
            trends=trends,
            filters_applied=filters,
            cached=False
        )

        cache_key = cls._build_cache_key(filters)
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
    def _empty_payload(cls, filters: Dict[str, Any]) -> CapacityAnalyticsPayload:
        return CapacityAnalyticsPayload(
            overview=CapacityOverviewMetrics(
                overall_network_capacity=0.0, avg_hub_capacity=0.0, avg_repair_center_capacity=0.0,
                available_capacity=0.0, used_capacity=0.0, capacity_utilization_pct=0.0,
                capacity_growth=0.0, capacity_availability=100.0
            ),
            hubs_analysis=[],
            repair_centers_analysis=[],
            regional_analysis=RegionalCapacityBreakdown(),
            bottlenecks=CapacityBottlenecks(),
            rankings=CapacityRankings(),
            trends=CapacityTrends(),
            filters_applied=filters,
            cached=False
        )
