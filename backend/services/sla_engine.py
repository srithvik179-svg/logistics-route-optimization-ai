"""SLA Analytics Engine — Orchestrator with in-memory caching.

Primary entry point for SLA compliance analysis. Loads processed datasets,
evaluates SLA rules, and coordinates sub-services for breakdowns, rankings,
violations, and trends.
"""

import json
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime

from backend.config import SLAConfig
from backend.services.repository import repository
from backend.services.geospatial_service import GeospatialService
from backend.services.sla_statistics import SLAStatistics
from backend.services.sla_rankings import SLARankingService
from backend.services.sla_violations import SLAViolationService
from backend.services.sla_trends import SLATrendsService
from backend.models.sla_metrics import (
    SLAAnalyticsPayload,
    SLAOverviewMetrics,
    SLADimensionalBreakdowns,
    SLARankings,
    SLAOutliersAndViolations,
    SLATrends,
)
from backend.utils.logger import logger


class SLAEngine:
    """Orchestrates Service Level Agreement (SLA) analytics across the network.

    Responsibilities:
        1. Loads processed sheets from Repository.
        2. Computes transit durations dynamically.
        3. Configures operating thresholds from SLAConfig.
        4. Calculates compliance rates and breakdowns.
        5. Delegates violations, rankings, and trends calculations.
        6. Caches calculated payloads.
    """

    _cache: Dict[str, SLAAnalyticsPayload] = {}

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the in-memory cache."""
        cls._cache.clear()
        logger.info("SLAEngine: Cache cleared.")

    @classmethod
    def get_sla_payload(cls, filters: Dict[str, Any]) -> SLAAnalyticsPayload:
        """Main entry point returning a fully computed SLAAnalyticsPayload.

        Args:
            filters: Global filters dictionary.

        Returns:
            SLAAnalyticsPayload payload.
        """
        logger.info(f"SLAEngine: SLA Engine Started. Filters: {filters}")

        # --- Cache Lookup ---
        cache_key = cls._build_cache_key(filters)
        if cache_key in cls._cache:
            logger.info("SLAEngine: Cache HIT — returning cached payload.")
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
            logger.warning("SLAEngine: Empty dataset after filtering.")
            empty = cls._empty_payload(filters)
            cls._cache[cache_key] = empty
            return empty

        # Compute transit days (in case not already calculated)
        df_filtered = cls._compute_transit_days(df_filtered)

        # Get configurable limit
        transit_limit = SLAConfig.TRANSIT_TIME_LIMIT

        # --- 1. Compliance KPIs (delegated) ---
        overview = SLAStatistics.compute_overview(df_filtered, transit_limit)
        logger.info("SLAEngine: Compliance Calculated.")

        # --- 2. Dimensional breakdowns (delegated) ---
        breakdowns = SLAStatistics.compute_breakdowns(df_filtered, df_hub, df_tpr, df_parts, transit_limit)

        # --- 3. Violation Analysis (delegated) ---
        violations = SLAViolationService.analyze_violations(df_filtered, df_parts, transit_limit, top_n=5)
        logger.info("SLAEngine: Violations Detected.")

        # --- 4. Rankings (delegated) ---
        rankings = SLARankingService.generate_rankings(breakdowns, top_n=5)
        logger.info("SLAEngine: Rankings Generated.")

        # --- 5. Trends (delegated) ---
        trends = SLATrendsService.generate_trends(df_filtered, transit_limit)
        logger.info("SLAEngine: Trend Datasets Generated.")

        payload = SLAAnalyticsPayload(
            overview=overview,
            breakdowns=breakdowns,
            violations_analysis=violations,
            rankings=rankings,
            trends=trends,
            filters_applied=filters,
            cached=False
        )

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
    def _compute_transit_days(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Computes Transit_Days = Delivery_Date - Order_Date."""
        if "Order_Date" not in df.columns or "Delivery_Date" not in df.columns:
            df["Transit_Days"] = 0.0
            return df

        df = df.copy()
        order = pd.to_datetime(df["Order_Date"], errors="coerce")
        delivery = pd.to_datetime(df["Delivery_Date"], errors="coerce")
        df["Transit_Days"] = (delivery - order).dt.total_seconds() / 86400.0
        df["Transit_Days"] = df["Transit_Days"].fillna(0.0).clip(lower=0.0)
        return df

    @classmethod
    def _empty_payload(cls, filters: Dict[str, Any]) -> SLAAnalyticsPayload:
        return SLAAnalyticsPayload(
            overview=SLAOverviewMetrics(
                overall_compliance_pct=0.0, total_shipments=0, sla_met_count=0,
                sla_violations=0, avg_delay_beyond_sla=0.0, avg_early_completion=0.0,
                sla_success_rate=0.0
            ),
            breakdowns=SLADimensionalBreakdowns(),
            violations_analysis=SLAOutliersAndViolations(),
            rankings=SLARankings(),
            trends=SLATrends(),
            filters_applied=filters,
            cached=False
        )
