"""Transit Time Analytics Engine — Orchestrator with in-memory caching.

Primary entry point for all transit time analytics. Loads and enriches
transaction data from the Repository Layer, computes transit days, delegates
to sub-services, and caches the full TransitAnalyticsPayload.
"""

import json
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime

from backend.services.repository import repository
from backend.services.geospatial_service import GeospatialService
from backend.services.transit_statistics import TransitStatistics
from backend.services.transit_distribution import TransitDistributionService
from backend.services.transit_rankings import TransitRankingService
from backend.services.transit_outliers import TransitOutlierDetector
from backend.models.transit_metrics import (
    TransitAnalyticsPayload,
    TransitOverviewMetrics,
    TransitDistribution,
    TransitRankings,
    TransitTrends,
    TransitTrendPoint,
    TransitOutliers,
    TransitBreakdownItem,
)
from backend.utils.logger import logger


class TransitEngine:
    """Orchestrates transit time analysis across the entire logistics network.

    Responsibilities:
        1. Load and enrich transaction data from the Repository Layer.
        2. Compute transit days (Delivery_Date - Order_Date).
        3. Calculate 13 overview metrics.
        4. Delegate distribution analysis to TransitDistributionService.
        5. Delegate ranking generation to TransitRankingService.
        6. Generate time-series trend datasets.
        7. Delegate outlier detection to TransitOutlierDetector.
        8. Cache every payload to avoid repeated computation.
    """

    _cache: Dict[str, TransitAnalyticsPayload] = {}

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the in-memory analytics cache."""
        cls._cache.clear()
        logger.info("TransitEngine: Cache cleared.")

    @classmethod
    def get_transit_analytics(cls, filters: Dict[str, Any]) -> TransitAnalyticsPayload:
        """Main entry point — returns a fully computed TransitAnalyticsPayload.

        Args:
            filters: Optional filter dict (start_date, end_date, hub, partner, etc.)

        Returns:
            TransitAnalyticsPayload with overview, distribution, rankings, trends, outliers.
        """
        logger.info(f"TransitEngine: Transit Engine Started. Filters: {filters}")

        # --- Cache Lookup ---
        cache_key = cls._build_cache_key(filters)
        if cache_key in cls._cache:
            logger.info("TransitEngine: Cache HIT — returning cached payload.")
            cached = cls._cache[cache_key]
            cached.cached = True
            return cached

        # --- Load & Enrich Data ---
        df = cls._load_and_enrich()

        if len(df) == 0:
            logger.warning("TransitEngine: No transaction data available.")
            empty = cls._empty_payload(filters)
            cls._cache[cache_key] = empty
            return empty

        # --- Apply Filters ---
        df_parts = repository._processed_sheets.get("Parts_Master", pd.DataFrame())
        df_filtered = GeospatialService._apply_geospatial_filters(df, df_parts, filters)

        if len(df_filtered) == 0:
            logger.warning("TransitEngine: Filters produced empty result set.")
            empty = cls._empty_payload(filters)
            cls._cache[cache_key] = empty
            return empty

        # --- Compute Transit Days ---
        df_filtered = cls._compute_transit_days(df_filtered)

        transit_series = df_filtered["Transit_Days"]

        # --- Overview Metrics ---
        overview = cls._calculate_overview(df_filtered, transit_series)
        logger.info("TransitEngine: Transit Metrics Generated event logged.")

        # --- Distribution (delegated) ---
        distribution = TransitDistributionService.generate_distribution(transit_series)

        # --- Rankings (delegated) ---
        rankings = TransitRankingService.generate_rankings(df_filtered, transit_col="Transit_Days", top_n=5)

        # --- Trends ---
        trends = cls._generate_trends(df_filtered)

        # --- Outliers (delegated) ---
        outliers = TransitOutlierDetector.detect_outliers(df_filtered, transit_col="Transit_Days")

        # --- Assemble Payload ---
        payload = TransitAnalyticsPayload(
            overview=overview,
            distribution=distribution,
            rankings=rankings,
            trends=trends,
            outliers=outliers,
            filters_applied=filters,
            cached=False,
        )

        cls._cache[cache_key] = payload
        logger.info("TransitEngine: Payload cached and ready for consumption.")
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
        """Loads processed transactions and enriches with derived fields."""
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

        return df

    @classmethod
    def _compute_transit_days(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Computes Transit_Days = Delivery_Date - Order_Date."""
        if "Order_Date" not in df.columns or "Delivery_Date" not in df.columns:
            logger.warning("TransitEngine: Missing date columns. Setting Transit_Days to 0.")
            df["Transit_Days"] = 0.0
            return df

        df = df.copy()
        order = pd.to_datetime(df["Order_Date"], errors="coerce")
        delivery = pd.to_datetime(df["Delivery_Date"], errors="coerce")
        df["Transit_Days"] = (delivery - order).dt.total_seconds() / 86400.0
        df["Transit_Days"] = df["Transit_Days"].fillna(0.0).clip(lower=0.0)
        return df

    @classmethod
    def _calculate_overview(cls, df: pd.DataFrame, transit_series: pd.Series) -> TransitOverviewMetrics:
        """Calculates the 13 overview transit KPIs."""
        stats = TransitStatistics.compute_stats(transit_series)

        total_shipments = len(df)

        # Per-dimension averages
        def _group_mean(col: str) -> float:
            if col not in df.columns:
                return 0.0
            grp = df.groupby(col)["Transit_Days"].mean()
            return round(float(grp.mean()), 2) if len(grp) > 0 else 0.0

        # Route average
        routes = df["Origin_Hub"] + " → " + df["Destination_Hub"]
        route_avgs = df.groupby(routes)["Transit_Days"].mean()
        avg_route = round(float(route_avgs.mean()), 2) if len(route_avgs) > 0 else 0.0

        return TransitOverviewMetrics(
            avg_transit_time=stats["avg"],
            median_transit_time=stats["median"],
            min_transit_time=stats["min"],
            max_transit_time=stats["max"],
            transit_variance=stats["variance"],
            transit_std_deviation=stats["std_deviation"],
            total_shipments=total_shipments,
            avg_transit_per_route=avg_route,
            avg_transit_per_hub=_group_mean("Origin_Hub"),
            avg_transit_per_repair_center=_group_mean("TPR_ID"),
            avg_transit_per_partner=_group_mean("Logistics_Partner"),
            avg_transit_per_priority=_group_mean("Priority"),
            avg_transit_per_flow_type=_group_mean("Flow_Type"),
        )

    @classmethod
    def _generate_trends(cls, df: pd.DataFrame) -> TransitTrends:
        """Generates daily, weekly, monthly, and quarterly transit performance trends."""
        logger.info("TransitEngine: Generating transit trend datasets.")

        if "Order_Date" not in df.columns or "Transit_Days" not in df.columns:
            logger.warning("TransitEngine: Missing columns for trend generation.")
            return TransitTrends()

        df_work = df.copy()
        df_work["Order_Date"] = pd.to_datetime(df_work["Order_Date"], errors="coerce")
        df_work = df_work.dropna(subset=["Order_Date", "Transit_Days"])

        if len(df_work) == 0:
            return TransitTrends()

        has_sla = "SLA_Status" in df_work.columns
        df_work = df_work.sort_values("Order_Date")

        trends = TransitTrends()
        trends.daily = cls._aggregate_trend(df_work, "D", "%Y-%m-%d", has_sla)
        trends.weekly = cls._aggregate_trend(df_work, "W", "%Y-W%U", has_sla)
        trends.monthly = cls._aggregate_trend(df_work, "MS", "%Y-%m", has_sla)
        trends.quarterly = cls._aggregate_trend(df_work, "QS", "Q", has_sla)

        return trends

    @classmethod
    def _aggregate_trend(
        cls,
        df: pd.DataFrame,
        freq: str,
        fmt: str,
        has_sla: bool,
    ) -> List[TransitTrendPoint]:
        """Aggregates transit data by a pandas frequency string."""
        points: List[TransitTrendPoint] = []

        for period, group in df.set_index("Order_Date").resample(freq):
            if len(group) == 0:
                continue

            if freq == "QS":
                qn = (period.month - 1) // 3 + 1
                label = f"{period.year}-Q{qn}"
            else:
                label = period.strftime(fmt)

            avg_t = round(float(group["Transit_Days"].mean()), 2)
            total = int(len(group))
            on_time = 0.0
            if has_sla and "SLA_Status" in group.columns:
                met = int((group["SLA_Status"] == "MET").sum())
                on_time = round((met / total) * 100, 1) if total > 0 else 0.0

            points.append(TransitTrendPoint(
                period=label,
                avg_transit_time=avg_t,
                total_shipments=total,
                on_time_pct=on_time,
            ))

        return points

    @classmethod
    def _empty_payload(cls, filters: Dict[str, Any]) -> TransitAnalyticsPayload:
        """Returns a zeroed-out payload for empty data scenarios."""
        return TransitAnalyticsPayload(
            overview=TransitOverviewMetrics(
                avg_transit_time=0.0, median_transit_time=0.0, min_transit_time=0.0,
                max_transit_time=0.0, transit_variance=0.0, transit_std_deviation=0.0,
                total_shipments=0, avg_transit_per_route=0.0, avg_transit_per_hub=0.0,
                avg_transit_per_repair_center=0.0, avg_transit_per_partner=0.0,
                avg_transit_per_priority=0.0, avg_transit_per_flow_type=0.0,
            ),
            distribution=TransitDistribution(),
            rankings=TransitRankings(),
            trends=TransitTrends(),
            outliers=TransitOutliers(),
            filters_applied=filters,
            cached=False,
        )
