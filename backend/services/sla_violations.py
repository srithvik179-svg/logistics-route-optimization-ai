"""Violation analysis service identifying repeated violations, critical delay locations, partners, and parts."""

import pandas as pd
from typing import List, Dict, Any
from backend.models.sla_metrics import SLAOutliersAndViolations, ViolationEntity
from backend.utils.logger import logger


class SLAViolationService:
    """Detects repeated violations and critical delay entities.

    Stateless service designed for reusability.
    """

    @classmethod
    def analyze_violations(
        cls,
        df: pd.DataFrame,
        parts_df: pd.DataFrame,
        transit_limit: float = 3.0,
        top_n: int = 5
    ) -> SLAOutliersAndViolations:
        """Flags high-delay routes, locations, partners, and parts.

        Args:
            df: Enriched transactions DataFrame.
            parts_df: Parts Master DataFrame.
            transit_limit: Configure SLA transit limit.
            top_n: Limit on returned violation entities.

        Returns:
            SLAOutliersAndViolations payload container.
        """
        logger.info("SLAViolationService: Scanning for SLA violations.")

        outliers = SLAOutliersAndViolations()
        
        # Select violated transactions (Transit_Days > limit)
        violated_df = df[df["Transit_Days"] > transit_limit].copy()
        outliers.total_violations_recorded = len(violated_df)

        if len(violated_df) == 0:
            return outliers

        # Helper region map
        df_work = df.copy()
        violated_df["Delay_Days"] = violated_df["Transit_Days"] - transit_limit

        # 1. High Delay Routes
        violated_df["Route_Key"] = violated_df["Origin_Hub"] + " → " + violated_df["Destination_Hub"]
        route_delays = violated_df.groupby("Route_Key").agg(
            violation_count=("Transaction_ID", "count"),
            avg_delay=("Delay_Days", "mean")
        ).reset_index()
        outliers.high_delay_routes = cls._build_violation_list(route_delays, "Route_Key", top_n)

        # 2. Repeated SLA Violations (at locations - Origin Hubs)
        loc_delays = violated_df.groupby("Origin_Hub").agg(
            violation_count=("Transaction_ID", "count"),
            avg_delay=("Delay_Days", "mean")
        ).reset_index()
        outliers.repeated_sla_violations = cls._build_violation_list(loc_delays, "Origin_Hub", top_n)

        # 3. Critical Delay Locations (Origin or Destination Hubs with highest average delay)
        # Combine origin and destination occurrences of delay
        all_locs = []
        for loc, grp in violated_df.groupby("Origin_Hub"):
            all_locs.append({"loc": loc, "count": len(grp), "delay": float(grp["Delay_Days"].mean())})
        for loc, grp in violated_df.groupby("Destination_Hub"):
            all_locs.append({"loc": loc, "count": len(grp), "delay": float(grp["Delay_Days"].mean())})
        
        loc_combined = pd.DataFrame(all_locs)
        if len(loc_combined) > 0:
            loc_combined_agg = loc_combined.groupby("loc").agg(
                violation_count=("count", "sum"),
                avg_delay=("delay", "mean")
            ).reset_index()
            outliers.critical_delay_locations = cls._build_violation_list(loc_combined_agg, "loc", top_n)

        # 4. Critical Logistics Partners
        partner_delays = violated_df.groupby("Logistics_Partner").agg(
            violation_count=("Transaction_ID", "count"),
            avg_delay=("Delay_Days", "mean")
        ).reset_index()
        outliers.critical_logistics_partners = cls._build_violation_list(partner_delays, "Logistics_Partner", top_n)

        # 5. Frequently Delayed Parts
        # Merge category
        violated_parts = violated_df.copy()
        if len(parts_df) > 0 and "Part_Number" in parts_df.columns and "Category" in parts_df.columns:
            violated_parts = violated_parts.merge(parts_df[["Part_Number", "Category"]], on="Part_Number", how="left", suffixes=("", "_parts_master"))
        else:
            violated_parts["Category"] = "Unknown"

        part_delays = violated_parts.groupby("Part_Number").agg(
            violation_count=("Transaction_ID", "count"),
            avg_delay=("Delay_Days", "mean")
        ).reset_index()
        outliers.frequently_delayed_parts = cls._build_violation_list(part_delays, "Part_Number", top_n)

        logger.info("SLAViolationService: Violations Detected.")
        return outliers

    @classmethod
    def _build_violation_list(cls, grouped_df: pd.DataFrame, key_col: str, top_n: int) -> List[ViolationEntity]:
        # Sort by count descending, then by average delay descending
        sorted_df = grouped_df.sort_values(by=["violation_count", "avg_delay"], ascending=False).head(top_n)

        items = []
        for _, row in sorted_df.iterrows():
            avg_d = float(row["avg_delay"])
            cnt = int(row["violation_count"])
            
            # Risk assessment
            if cnt >= 5 or avg_d > 2.0:
                risk = "Critical"
            elif cnt >= 3 or avg_d > 1.0:
                risk = "High"
            elif cnt >= 2 or avg_d > 0.5:
                risk = "Medium"
            else:
                risk = "Low"

            items.append(ViolationEntity(
                name=str(row[key_col]),
                violation_count=cnt,
                avg_delay_days=round(avg_d, 2),
                risk_level=risk
            ))
        return items
