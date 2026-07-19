"""Stateless descriptive statistics and dimensional breakdowns for network capacity."""

import pandas as pd
from typing import List, Dict, Any, Tuple
from backend.utils.logger import logger
from backend.models.capacity_metrics import (
    CapacityOverviewMetrics,
    NodeCapacityMetrics,
    RegionalCapacityBreakdown,
    RegionalCapacityDimension,
)


class CapacityStatistics:
    """Computes descriptive metrics and dimensional breakdowns for network capacity.

    Stateless service designed for dependency injection.
    """

    @classmethod
    def compute_overview(
        cls,
        hubs_analysis: List[NodeCapacityMetrics],
        rcs_analysis: List[NodeCapacityMetrics],
        starting_baseline: float = 23000.0
    ) -> CapacityOverviewMetrics:
        """Calculates top-level network capacity KPIs.

        Args:
            hubs_analysis: List of hub capacity metrics.
            rcs_analysis: List of repair center capacity metrics.
            starting_baseline: Historical baseline capacity to calculate growth.

        Returns:
            CapacityOverviewMetrics payload.
        """
        logger.info("CapacityStatistics: Computing network capacity overview metrics.")

        total_h_cap = sum(h.capacity for h in hubs_analysis)
        total_rc_cap = sum(rc.capacity for rc in rcs_analysis)
        total_cap = total_h_cap + total_rc_cap

        avg_h_cap = total_h_cap / len(hubs_analysis) if len(hubs_analysis) > 0 else 0.0
        avg_rc_cap = total_rc_cap / len(rcs_analysis) if len(rcs_analysis) > 0 else 0.0

        used_h = sum(h.used_capacity for h in hubs_analysis)
        used_rc = sum(rc.used_capacity for rc in rcs_analysis)
        used_cap = used_h + used_rc

        avail_cap = total_cap - used_cap
        util_pct = (used_cap / total_cap) * 100.0 if total_cap > 0 else 0.0
        avail_pct = (avail_cap / total_cap) * 100.0 if total_cap > 0 else 0.0

        # Simulate capacity growth rate relative to historical starting baseline
        growth = ((total_cap - starting_baseline) / starting_baseline) * 100.0 if starting_baseline > 0 else 0.0

        return CapacityOverviewMetrics(
            overall_network_capacity=round(total_cap, 2),
            avg_hub_capacity=round(avg_h_cap, 2),
            avg_repair_center_capacity=round(avg_rc_cap, 2),
            available_capacity=round(avail_cap, 2),
            used_capacity=round(used_cap, 2),
            capacity_utilization_pct=round(util_pct, 1),
            capacity_growth=round(growth, 2),
            capacity_availability=round(avail_pct, 1)
        )

    @classmethod
    def compute_regional_analysis(
        cls,
        nodes_analysis: List[NodeCapacityMetrics],
        hub_df: pd.DataFrame,
        tpr_df: pd.DataFrame,
        tx_df: pd.DataFrame
    ) -> RegionalCapacityBreakdown:
        """Aggregates capacity utilization metrics across regional, city, hub type, flow, and partner dimensions.

        Args:
            nodes_analysis: Mixed list of hub and RC metrics.
            hub_df: Hub Master DataFrame.
            tpr_df: TPR Master DataFrame.
            tx_df: Transactions DataFrame.

        Returns:
            RegionalCapacityBreakdown with multi-dimensional maps.
        """
        logger.info("CapacityStatistics: Generating multi-dimensional regional capacity breakdowns.")

        breakdown = RegionalCapacityBreakdown()

        # Build location dictionary for fast lookups
        node_map = {n.node_id: n for n in nodes_analysis}

        # Helper maps
        hub_regions = {}
        hub_cities = {}
        if len(hub_df) > 0 and "Hub_ID" in hub_df.columns:
            if "Region" in hub_df.columns:
                hub_regions = dict(zip(hub_df["Hub_ID"], hub_df["Region"]))
            if "City" in hub_df.columns:
                hub_cities = dict(zip(hub_df["Hub_ID"], hub_df["City"]))

        tpr_regions = {}
        tpr_cities = {}
        tpr_names = {}
        if len(tpr_df) > 0 and "TPR_ID" in tpr_df.columns:
            if "Coverage_Region" in tpr_df.columns:
                tpr_regions = dict(zip(tpr_df["TPR_ID"], tpr_df["Coverage_Region"]))
            if "TPR_Name" in tpr_df.columns:
                tpr_names = dict(zip(tpr_df["TPR_ID"], tpr_df["TPR_Name"]))
            # COORDINATES_FALLBACK city mapper
            from backend.services.geospatial_service import GeospatialService
            for rc_id in tpr_df["TPR_ID"].unique():
                tpr_cities[rc_id] = GeospatialService.COORDINATES_FALLBACK.get(rc_id, {}).get("city") or "Unknown"

        # 1. By Region & City
        reg_cap: Dict[str, List[float]] = {}  # region -> [cap, used]
        city_cap: Dict[str, List[float]] = {}  # city -> [cap, used]

        for node_id, node in node_map.items():
            reg = hub_regions.get(node_id) or tpr_regions.get(node_id) or "Unknown"
            city = hub_cities.get(node_id) or tpr_cities.get(node_id) or "Unknown"

            r_vals = reg_cap.get(reg, [0.0, 0.0])
            r_vals[0] += node.capacity
            r_vals[1] += node.used_capacity
            reg_cap[reg] = r_vals

            c_vals = city_cap.get(city, [0.0, 0.0])
            c_vals[0] += node.capacity
            c_vals[1] += node.used_capacity
            city_cap[city] = c_vals

        breakdown.by_region = cls._build_dimension_map(reg_cap)
        breakdown.by_city = cls._build_dimension_map(city_cap)

        # 2. By Hub Type
        hub_type_cap: Dict[str, List[float]] = {}
        from backend.services.geospatial_service import GeospatialService
        for node_id, node in node_map.items():
            h_type = GeospatialService.COORDINATES_FALLBACK.get(node_id, {}).get("type") or "Regional Node"
            vals = hub_type_cap.get(h_type, [0.0, 0.0])
            vals[0] += node.capacity
            vals[1] += node.used_capacity
            hub_type_cap[h_type] = vals
        breakdown.by_hub_type = cls._build_dimension_map(hub_type_cap)

        # 3. By Logistics Partner
        partner_cap: Dict[str, List[float]] = {}
        for node_id, node in node_map.items():
            if node_id in tpr_names:
                p_name = tpr_names[node_id]
                vals = partner_cap.get(p_name, [0.0, 0.0])
                vals[0] += node.capacity
                vals[1] += node.used_capacity
                partner_cap[p_name] = vals
        breakdown.by_logistics_partner = cls._build_dimension_map(partner_cap)

        # 4. By Flow Type (capacity load divided by Flow Types)
        flow_cap: Dict[str, List[float]] = {}
        if len(tx_df) > 0 and "Flow_Type" in tx_df.columns:
            for f_type, group in tx_df.groupby("Flow_Type"):
                qty = float(group["Quantity"].sum())
                # Flow type capacity utilization is simulated from flows
                # Flow has nominal baseline capacity of 10000.0 units
                flow_cap[str(f_type)] = [10000.0, qty]
        breakdown.by_flow_type = cls._build_dimension_map(flow_cap)

        return breakdown

    @classmethod
    def _build_dimension_map(cls, raw_map: Dict[str, List[float]]) -> Dict[str, RegionalCapacityDimension]:
        res = {}
        for k, v in raw_map.items():
            cap, used = v[0], v[1]
            util = (used / cap) * 100.0 if cap > 0 else 0.0
            res[k] = RegionalCapacityDimension(
                capacity=round(cap, 2),
                used=round(used, 2),
                utilization_pct=round(util, 1)
            )
        return res
