"""Ranking generator for logistics network capacity comparisons."""

from typing import List
from backend.models.capacity_metrics import CapacityRankingEntry, CapacityRankings, NodeCapacityMetrics, RegionalCapacityBreakdown
from backend.utils.logger import logger


class CapacityRankingService:
    """Generates capacity utilization and volume rankings across hubs, RCs, and regions.

    Stateless service with class-level methods.
    """

    @classmethod
    def generate_rankings(
        cls,
        hubs_analysis: List[NodeCapacityMetrics],
        rcs_analysis: List[NodeCapacityMetrics],
        regional_analysis: RegionalCapacityBreakdown,
        top_n: int = 5
    ) -> CapacityRankings:
        """Generates sorted rankings lists for hubs, RCs, and regions.

        Args:
            hubs_analysis: List of hub capacity metrics.
            rcs_analysis: List of RC capacity metrics.
            regional_analysis: Regional capacity breakdown containing aggregated regions.
            top_n: Max length of ranking lists.

        Returns:
            CapacityRankings payload container.
        """
        logger.info(f"CapacityRankingService: Generating rankings (top_n={top_n}).")

        rankings = CapacityRankings()

        # 1. Hub Rankings
        if len(hubs_analysis) > 0:
            top_h = sorted(hubs_analysis, key=lambda x: x.utilization_pct, reverse=True)[:top_n]
            rankings.top_utilized_hubs = [
                CapacityRankingEntry(rank=i + 1, entity_name=h.node_id, metric_value=h.utilization_pct, capacity=h.capacity)
                for i, h in enumerate(top_h)
            ]

            least_h = sorted(hubs_analysis, key=lambda x: x.utilization_pct)[:top_n]
            rankings.least_utilized_hubs = [
                CapacityRankingEntry(rank=i + 1, entity_name=h.node_id, metric_value=h.utilization_pct, capacity=h.capacity)
                for i, h in enumerate(least_h)
            ]

        # 2. Repair Center Rankings
        if len(rcs_analysis) > 0:
            top_rc = sorted(rcs_analysis, key=lambda x: x.utilization_pct, reverse=True)[:top_n]
            rankings.top_utilized_repair_centers = [
                CapacityRankingEntry(rank=i + 1, entity_name=rc.node_id, metric_value=rc.utilization_pct, capacity=rc.capacity)
                for i, rc in enumerate(top_rc)
            ]

            least_rc = sorted(rcs_analysis, key=lambda x: x.utilization_pct)[:top_n]
            rankings.least_utilized_repair_centers = [
                CapacityRankingEntry(rank=i + 1, entity_name=rc.node_id, metric_value=rc.utilization_pct, capacity=rc.capacity)
                for i, rc in enumerate(least_rc)
            ]

        # 3. Regional Rankings
        if regional_analysis and regional_analysis.by_region:
            reg_items = [
                {"name": name, "cap": dim.capacity}
                for name, dim in regional_analysis.by_region.items()
            ]

            top_reg = sorted(reg_items, key=lambda x: x["cap"], reverse=True)[:top_n]
            rankings.highest_capacity_regions = [
                CapacityRankingEntry(rank=i + 1, entity_name=r["name"], metric_value=r["cap"], capacity=r["cap"])
                for i, r in enumerate(top_reg)
            ]

            least_reg = sorted(reg_items, key=lambda x: x["cap"])[:top_n]
            rankings.lowest_capacity_regions = [
                CapacityRankingEntry(rank=i + 1, entity_name=r["name"], metric_value=r["cap"], capacity=r["cap"])
                for i, r in enumerate(least_reg)
            ]

        logger.info("CapacityRankingService: Capacity Rankings Generated.")
        return rankings
