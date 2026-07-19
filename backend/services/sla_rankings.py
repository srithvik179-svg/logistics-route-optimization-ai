"""Ranking generator for Service Level Agreement performance comparisons."""

from typing import List
from backend.models.sla_metrics import SLARankingEntry, SLARankings, SLADimensionalBreakdowns, SLADimensionItem
from backend.utils.logger import logger


class SLARankingService:
    """Generates reliability and SLA compliance rankings for hubs, RCs, partners, and routes.

    Stateless service with class-level methods.
    """

    @classmethod
    def generate_rankings(
        cls,
        breakdowns: SLADimensionalBreakdowns,
        top_n: int = 5
    ) -> SLARankings:
        """Constructs sorted SLA compliance rank lists.

        Args:
            breakdowns: Container of calculated SLA breakdowns.
            top_n: Size limit of ranking lists.

        Returns:
            SLARankings payload container.
        """
        logger.info(f"SLARankingService: Generating rankings (top_n={top_n}).")

        rankings = SLARankings()

        # Best / Worst Hubs
        if breakdowns.by_hub:
            rankings.best_performing_hubs = cls._rank(breakdowns.by_hub, top_n, reverse=True)
            rankings.worst_performing_hubs = cls._rank(breakdowns.by_hub, top_n, reverse=False)

        # Best / Worst Partners
        if breakdowns.by_partner:
            rankings.best_logistics_partners = cls._rank(breakdowns.by_partner, top_n, reverse=True)
            rankings.worst_logistics_partners = cls._rank(breakdowns.by_partner, top_n, reverse=False)

        # Best / Worst Repair Centers
        if breakdowns.by_repair_center:
            rankings.best_repair_centers = cls._rank(breakdowns.by_repair_center, top_n, reverse=True)
            rankings.worst_repair_centers = cls._rank(breakdowns.by_repair_center, top_n, reverse=False)

        # Reliable / Unreliable Routes
        if breakdowns.by_route:
            rankings.most_reliable_routes = cls._rank(breakdowns.by_route, top_n, reverse=True)
            rankings.least_reliable_routes = cls._rank(breakdowns.by_route, top_n, reverse=False)

        logger.info("SLARankingService: Rankings Generated.")
        return rankings

    @classmethod
    def _rank(cls, items: List[SLADimensionItem], top_n: int, reverse: bool) -> List[SLARankingEntry]:
        # Sort first by compliance rate, then by total shipments (to break ties reliably)
        sorted_items = sorted(
            items,
            key=lambda x: (x.compliance_pct, x.total_count),
            reverse=reverse
        )[:top_n]

        entries = []
        for i, item in enumerate(sorted_items):
            entries.append(SLARankingEntry(
                rank=i + 1,
                entity_name=item.name,
                compliance_pct=item.compliance_pct,
                total_shipments=item.total_count
            ))
        return entries
