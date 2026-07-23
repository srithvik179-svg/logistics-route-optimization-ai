"""Logistics Cost Analytics Engine — Orchestrator with in-memory caching.

This is the primary entry point for all cost analytics operations. It loads and
enriches transaction data from the Repository Layer, delegates to specialised
sub-services (CostStatistics, CostRanking, CostTrendsService), and caches the
full CostAnalyticsPayload to avoid repeated calculations.
"""

import json
import pandas as pd
from typing import Dict, Any, Optional, List
from datetime import datetime

from backend.services.repository import repository
from backend.services.geospatial_service import GeospatialService
from backend.services.cost_statistics import CostStatistics
from backend.services.cost_ranking import CostRanking
from backend.services.cost_trends import CostTrendsService
from backend.models.cost_metrics import (
    CostAnalyticsPayload,
    CostOverviewMetrics,
    CostBreakdowns,
    CostBreakdownItem,
    CostVarianceMetrics,
    CostRankings,
    CostTrends,
)
from backend.utils.logger import logger


class CostEngine:
    """Orchestrates deep logistics cost analysis across the entire network.
    
    Responsibilities:
        1. Load and enrich transaction data from the Repository Layer.
        2. Calculate 9 overview cost metrics.
        3. Generate 8 breakdown dimensions.
        4. Delegate variance analysis to CostStatistics.
        5. Delegate ranking generation to CostRanking.
        6. Delegate time-series trend generation to CostTrendsService.
        7. Cache every calculated payload to avoid repeated computation.
    """

    # In-memory cache: filter-key -> CostAnalyticsPayload
    _cache: Dict[str, CostAnalyticsPayload] = {}

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the in-memory analytics cache."""
        cls._cache.clear()
        logger.info("CostEngine: Cache cleared.")

    @classmethod
    def get_cost_analytics(cls, filters: Dict[str, Any]) -> CostAnalyticsPayload:
        """Main entry point — returns a fully computed CostAnalyticsPayload.
        
        Args:
            filters: Dict of optional filters (start_date, end_date, hub, partner, etc.)
            
        Returns:
            CostAnalyticsPayload containing overview, breakdowns, variance, rankings, trends.
        """
        logger.info(f"CostEngine: Cost Engine Started. Filters: {filters}")

        # --- Cache Lookup ---
        cache_key = cls._build_cache_key(filters)
        if cache_key in cls._cache:
            logger.info("CostEngine: Cache HIT — returning cached payload.")
            cached = cls._cache[cache_key]
            cached.cached = True
            return cached

        # --- Load & Enrich Data ---
        df = cls._load_and_enrich()

        if len(df) == 0:
            logger.warning("CostEngine: No transaction data available. Returning empty payload.")
            empty = cls._empty_payload(filters)
            cls._cache[cache_key] = empty
            return empty

        # --- Apply Filters ---
        df_parts = repository._processed_sheets.get("Parts_Master", pd.DataFrame())
        df_filtered = GeospatialService._apply_geospatial_filters(df, df_parts, filters)

        if len(df_filtered) == 0:
            logger.warning("CostEngine: Filters produced empty result set.")
            empty = cls._empty_payload(filters)
            cls._cache[cache_key] = empty
            return empty

        # --- Calculate Overview Metrics ---
        overview = cls._calculate_overview(df_filtered)
        logger.info("CostEngine: Metrics Generated event logged.")

        # --- Generate Breakdowns ---
        breakdowns = cls._generate_breakdowns(df_filtered)

        # --- Variance Analysis (delegated) ---
        variance = CostStatistics.compute_variance_metrics(df_filtered["Shipment_Cost"])

        # --- Rankings (delegated) ---
        rankings = CostRanking.generate_rankings(df_filtered, top_n=5)

        # --- Trends (delegated) ---
        trends = CostTrendsService.generate_trends(df_filtered)

        # --- Assemble Payload ---
        payload = CostAnalyticsPayload(
            overview=overview,
            breakdowns=breakdowns,
            variance=variance,
            rankings=rankings,
            trends=trends,
            filters_applied=filters,
            cached=False,
        )

        # --- Cache Result ---
        cls._cache[cache_key] = payload
        logger.info("CostEngine: Payload cached and ready for consumption.")

        return payload

    # ────────────────────────────────────────────
    # Private Helpers
    # ────────────────────────────────────────────

    @classmethod
    def _build_cache_key(cls, filters: Dict[str, Any]) -> str:
        """Builds a deterministic cache key from the filter dict."""
        sorted_items = sorted(
            ((k, v) for k, v in filters.items() if v),
            key=lambda x: x[0],
        )
        return json.dumps(sorted_items, default=str)

    @classmethod
    def _load_and_enrich(cls) -> pd.DataFrame:
        """Loads processed transactions from the Repository Layer and enriches with derived fields."""
        df_tx = repository._processed_sheets.get("Logistics_Transactions")
        df_tpr = repository._processed_sheets.get(
            "TPR_Master" if repository.sheet_exists("TPR_Master") else "Repair_Center_Master",
        )

        if df_tx is None or len(df_tx) == 0:
            return pd.DataFrame()

        if df_tpr is None:
            df_tpr = pd.DataFrame()

        df = df_tx.copy()

        # Enrich: Logistics Partner
        tpr_names = (
            list(df_tpr["TPR_Name"])
            if len(df_tpr) > 0 and "TPR_Name" in df_tpr.columns
            else ["Swift LogiCo", "Apex Freight", "LoneStar Delivery"]
        )
        df["Logistics_Partner"] = [tpr_names[i % len(tpr_names)] for i in range(len(df))]
        df["TPR_ID"] = df["Logistics_Partner"].map(GeospatialService.TPR_NAME_TO_ID).fillna("TPR-001")

        # Enrich: Priority & Flow Type
        priorities: List[str] = []
        flow_types: List[str] = []
        for _, row in df.iterrows():
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

        df["Priority"] = priorities
        df["Flow_Type"] = flow_types

        # Enrich: Region from Hub master
        df_hub = repository._processed_sheets.get("Hub_Location_Master", pd.DataFrame())
        if len(df_hub) > 0 and "Hub_ID" in df_hub.columns and "City" in df_hub.columns:
            hub_region_map = dict(zip(df_hub["Hub_ID"], df_hub["City"]))
            df["Region"] = df["Origin_Hub"].map(hub_region_map).fillna("Unknown")
        else:
            df["Region"] = "Unknown"

        return df

    @classmethod
    def _calculate_overview(cls, df: pd.DataFrame) -> CostOverviewMetrics:
        """Calculates the 9 overview cost KPIs."""
        costs = df["Shipment_Cost"]
        total_shipments = len(df)
        overall_cost = float(costs.sum())
        avg_shipment = float(costs.mean())

        # Average Route Cost
        routes = df["Origin_Hub"] + " → " + df["Destination_Hub"]
        route_avg = df.groupby(routes)["Shipment_Cost"].mean()
        avg_route = float(route_avg.mean()) if len(route_avg) > 0 else 0.0

        # Average Cost Per Hub
        hub_avg = df.groupby("Origin_Hub")["Shipment_Cost"].mean()
        avg_hub = float(hub_avg.mean()) if len(hub_avg) > 0 else 0.0

        # Average Cost Per Repair Center
        rc_avg = df.groupby("TPR_ID")["Shipment_Cost"].mean()
        avg_rc = float(rc_avg.mean()) if len(rc_avg) > 0 else 0.0

        # Average Cost Per Partner
        partner_avg = df.groupby("Logistics_Partner")["Shipment_Cost"].mean()
        avg_partner = float(partner_avg.mean()) if len(partner_avg) > 0 else 0.0

        # Average Cost Per Category (via Parts Master join)
        df_parts = repository._processed_sheets.get("Parts_Master", pd.DataFrame())
        avg_category = 0.0
        if len(df_parts) > 0 and "Part_Number" in df.columns and "Category" in df_parts.columns:
            merged = df.merge(df_parts[["Part_Number", "Category"]], on="Part_Number", how="left", suffixes=("", "_parts_master"))
            cat_avg = merged.groupby("Category")["Shipment_Cost"].mean()
            avg_category = float(cat_avg.mean()) if len(cat_avg) > 0 else 0.0

        # Average Cost Per Flow Type
        flow_avg = df.groupby("Flow_Type")["Shipment_Cost"].mean()
        avg_flow = float(flow_avg.mean()) if len(flow_avg) > 0 else 0.0

        return CostOverviewMetrics(
            overall_logistics_cost=round(overall_cost, 2),
            avg_shipment_cost=round(avg_shipment, 2),
            avg_route_cost=round(avg_route, 2),
            avg_cost_per_hub=round(avg_hub, 2),
            avg_cost_per_repair_center=round(avg_rc, 2),
            avg_cost_per_partner=round(avg_partner, 2),
            avg_cost_per_category=round(avg_category, 2),
            avg_cost_per_flow_type=round(avg_flow, 2),
            total_shipments=total_shipments,
        )

    @classmethod
    def _generate_breakdowns(cls, df: pd.DataFrame) -> CostBreakdowns:
        """Generates all 8 cost breakdown dimensions."""
        breakdowns = CostBreakdowns()

        # 1. By Hub (Origin)
        breakdowns.by_hub = cls._breakdown_by_column(df, "Origin_Hub")

        # 2. By Route
        df_route = df.copy()
        df_route["Route_Key"] = df_route["Origin_Hub"] + " → " + df_route["Destination_Hub"]
        breakdowns.by_route = cls._breakdown_by_column(df_route, "Route_Key")

        # 3. By Repair Center
        breakdowns.by_repair_center = cls._breakdown_by_column(df, "TPR_ID")

        # 4. By Partner
        breakdowns.by_partner = cls._breakdown_by_column(df, "Logistics_Partner")

        # 5. By Region
        if "Region" in df.columns:
            breakdowns.by_region = cls._breakdown_by_column(df, "Region")

        # 6. By Priority
        breakdowns.by_priority = cls._breakdown_by_column(df, "Priority")

        # 7. By Part Category
        df_parts = repository._processed_sheets.get("Parts_Master", pd.DataFrame())
        if len(df_parts) > 0 and "Part_Number" in df.columns and "Category" in df_parts.columns:
            merged = df.merge(df_parts[["Part_Number", "Category"]], on="Part_Number", how="left", suffixes=("", "_parts_master"))
            breakdowns.by_category = cls._breakdown_by_column(merged, "Category")

        # 8. By Shipment Status (SLA_Status)
        if "SLA_Status" in df.columns:
            breakdowns.by_status = cls._breakdown_by_column(df, "SLA_Status")

        return breakdowns

    @classmethod
    def _breakdown_by_column(cls, df: pd.DataFrame, column: str) -> List[CostBreakdownItem]:
        """Helper to group by a column and produce CostBreakdownItem list."""
        if column not in df.columns:
            logger.warning(f"CostEngine: Column '{column}' not found. Skipping breakdown.")
            return []

        grouped = df.groupby(column)["Shipment_Cost"].agg(["sum", "mean", "count"]).reset_index()
        grouped.columns = [column, "total_cost", "avg_cost", "shipment_count"]
        grouped = grouped.sort_values("total_cost", ascending=False)

        items: List[CostBreakdownItem] = []
        for _, row in grouped.iterrows():
            items.append(CostBreakdownItem(
                name=str(row[column]),
                total_cost=round(float(row["total_cost"]), 2),
                avg_cost=round(float(row["avg_cost"]), 2),
                shipment_count=int(row["shipment_count"]),
            ))
        return items

    @classmethod
    def _empty_payload(cls, filters: Dict[str, Any]) -> CostAnalyticsPayload:
        """Returns a zeroed-out payload for empty data scenarios."""
        return CostAnalyticsPayload(
            overview=CostOverviewMetrics(
                overall_logistics_cost=0.0, avg_shipment_cost=0.0, avg_route_cost=0.0,
                avg_cost_per_hub=0.0, avg_cost_per_repair_center=0.0, avg_cost_per_partner=0.0,
                avg_cost_per_category=0.0, avg_cost_per_flow_type=0.0, total_shipments=0,
            ),
            breakdowns=CostBreakdowns(),
            variance=CostVarianceMetrics(
                maximum=0.0, minimum=0.0, median=0.0,
                std_deviation=0.0, variance=0.0, q1=0.0, q3=0.0, iqr=0.0,
            ),
            rankings=CostRankings(),
            trends=CostTrends(),
            filters_applied=filters,
            cached=False,
        )
