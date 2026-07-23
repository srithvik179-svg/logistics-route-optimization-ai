"""Stateless descriptive statistics and breakdowns for SLA compliance."""

import pandas as pd
from typing import List, Dict, Any
from backend.utils.logger import logger
from backend.models.sla_metrics import (
    SLAOverviewMetrics,
    SLADimensionItem,
    SLADimensionalBreakdowns,
)


class SLAStatistics:
    """Computes descriptive metrics and dimensional breakdowns for Service Level Agreements (SLA).

    Stateless service designed for dependency injection.
    """

    @classmethod
    def compute_overview(cls, df: pd.DataFrame, transit_limit: float = 3.0) -> SLAOverviewMetrics:
        """Calculates top-level SLA compliance KPIs.

        Args:
            df: Enriched transactions DataFrame with Transit_Days and SLA_Status.
            transit_limit: Configure limit for transit.

        Returns:
            SLAOverviewMetrics payload.
        """
        logger.info("SLAStatistics: Computing SLA overview metrics.")

        total = len(df)
        if total == 0:
            return cls._empty_overview()

        # Compute MET/MISSED based on Transit_Days vs transit_limit
        met_mask = df["Transit_Days"] <= transit_limit
        met_count = int(met_mask.sum())
        violation_count = total - met_count

        compliance = (met_count / total) * 100.0

        # Average delay beyond SLA (for MISSED)
        missed_df = df[~met_mask]
        avg_delay = 0.0
        if len(missed_df) > 0:
            avg_delay = float((missed_df["Transit_Days"] - transit_limit).mean())

        # Average early completion (for MET)
        met_df = df[met_mask]
        avg_early = 0.0
        if len(met_df) > 0:
            avg_early = float((transit_limit - met_df["Transit_Days"]).mean())

        return SLAOverviewMetrics(
            overall_compliance_pct=round(compliance, 1),
            total_shipments=total,
            sla_met_count=met_count,
            sla_violations=violation_count,
            avg_delay_beyond_sla=round(avg_delay, 2),
            avg_early_completion=round(avg_early, 2),
            sla_success_rate=round(compliance, 1)
        )

    @classmethod
    def compute_breakdowns(
        cls,
        df: pd.DataFrame,
        hub_df: pd.DataFrame,
        tpr_df: pd.DataFrame,
        parts_df: pd.DataFrame,
        transit_limit: float = 3.0
    ) -> SLADimensionalBreakdowns:
        """Aggregates SLA compliance rates by hub, repair center, partner, route, region, priority, and category.

        Args:
            df: Enriched transactions DataFrame.
            hub_df: Hub Location Master DataFrame.
            tpr_df: TPR Master DataFrame.
            parts_df: Parts Master DataFrame.
            transit_limit: Transit SLA limit.

        Returns:
            SLADimensionalBreakdowns containing dimension lists.
        """
        logger.info("SLAStatistics: Generating dimensional SLA breakdowns.")

        breakdowns = SLADimensionalBreakdowns()
        if len(df) == 0:
            return breakdowns

        hubs = list(hub_df["Hub_ID"].unique()) if len(hub_df) > 0 else []
        rcs = list(tpr_df["TPR_ID"].unique()) if len(tpr_df) > 0 else []

        # Helper regions map
        hub_reg = dict(zip(hub_df["Hub_ID"], hub_df["Region"])) if len(hub_df) > 0 and "Region" in hub_df.columns else {}
        tpr_reg = dict(zip(tpr_df["TPR_ID"], tpr_df["Coverage_Region"])) if len(tpr_df) > 0 and "Coverage_Region" in tpr_df.columns else {}

        # Hub Region column
        df_work = df.copy()
        df_work["Region"] = df_work["Origin_Hub"].map(hub_reg).fillna(df_work["TPR_ID"].map(tpr_reg)).fillna("Unknown")

        # Parts Category merge
        if len(parts_df) > 0 and "Part_Number" in df_work.columns and "Category" in parts_df.columns:
            df_work = df_work.merge(parts_df[["Part_Number", "Category"]], on="Part_Number", how="left", suffixes=("", "_parts_master"))
        else:
            df_work["Category"] = "Unknown"

        # Hubs breakdown (Origin_Hub only)
        hub_tx = df_work[df_work["Origin_Hub"].isin(hubs) | df_work["Origin_Hub"].str.upper().str.startswith("HUB")]
        breakdowns.by_hub = cls._breakdown_by_column(hub_tx, "Origin_Hub", transit_limit)

        # Repair Centers breakdown
        rc_tx = df_work[df_work["TPR_ID"].isin(rcs) | ~df_work["Origin_Hub"].isin(hubs) & ~df_work["Origin_Hub"].str.upper().str.startswith("HUB")]
        breakdowns.by_repair_center = cls._breakdown_by_column(rc_tx, "TPR_ID", transit_limit)

        # Partner breakdown
        breakdowns.by_partner = cls._breakdown_by_column(df_work, "Logistics_Partner", transit_limit)

        # Route breakdown
        df_work["Route_Key"] = df_work["Origin_Hub"] + " → " + df_work["Destination_Hub"]
        breakdowns.by_route = cls._breakdown_by_column(df_work, "Route_Key", transit_limit)

        # Region breakdown
        breakdowns.by_region = cls._breakdown_by_column(df_work, "Region", transit_limit)

        # Priority breakdown
        breakdowns.by_priority = cls._breakdown_by_column(df_work, "Priority", transit_limit)

        # Category breakdown
        breakdowns.by_category = cls._breakdown_by_column(df_work, "Category", transit_limit)

        return breakdowns

    @classmethod
    def _breakdown_by_column(cls, df: pd.DataFrame, column: str, transit_limit: float) -> List[SLADimensionItem]:
        if column not in df.columns or len(df) == 0:
            return []

        items = []
        for name, group in df.groupby(column):
            tot = len(group)
            met = int((group["Transit_Days"] <= transit_limit).sum())
            missed = tot - met
            pct = (met / tot) * 100.0 if tot > 0 else 0.0

            items.append(SLADimensionItem(
                name=str(name),
                compliance_pct=round(pct, 1),
                total_count=tot,
                violations=missed
            ))

        # Sort by total count descending
        return sorted(items, key=lambda x: x.total_count, reverse=True)

    @classmethod
    def _empty_overview(cls) -> SLAOverviewMetrics:
        return SLAOverviewMetrics(
            overall_compliance_pct=0.0,
            total_shipments=0,
            sla_met_count=0,
            sla_violations=0,
            avg_delay_beyond_sla=0.0,
            avg_early_completion=0.0,
            sla_success_rate=0.0
        )
