"""Feature engineering service compiling normalized feature vectors for logistics route paths."""

from typing import List, Dict, Any
from backend.models.feature_vector import FeatureVector


class FeatureEngineeringService:
    """Calculates and normalizes features for route recommendation options."""

    @classmethod
    def extract_features(
        cls,
        path_nodes: List[str],
        distance: float,
        cost: float,
        transit_time: float,
        composite_score: float = 75.0
    ) -> FeatureVector:
        """Generates a normalized FeatureVector for a given candidate route.

        Args:
            path_nodes: Ordered node IDs sequence.
            distance: Route distance.
            cost: Route cost.
            transit_time: Route transit time in days.
            composite_score: Pre-calculated composite score.

        Returns:
            FeatureVector: Computed features model.
        """
        # Normalization calculations (caps at 1.0)
        norm_cost = min(cost / 500.0, 1.0)
        norm_time = min(transit_time / 5.0, 1.0)

        # Estimate SLA compliance probability (assume 95% if below standard 3-day window)
        sla_prob = 0.98 if transit_time <= 3.0 else max(1.0 - (transit_time - 3.0) * 0.3, 0.0)

        # Approximate historical reliability based on path hops (shorter paths are usually more reliable)
        hops = len(path_nodes) - 1
        reliability = max(1.0 - hops * 0.05, 0.70)

        # Partner performance rating approximation
        partner_perf = 0.88 if hops <= 2 else 0.80

        # Calculate operational efficiency
        oper_eff = round(reliability * 0.5 + partner_perf * 0.5, 4)

        return FeatureVector(
            cost=round(norm_cost, 4),
            transit_time=round(norm_time, 4),
            distance=round(distance, 2),
            capacity_utilization=0.85,
            sla_compliance=round(sla_prob, 4),
            reliability=round(reliability, 4),
            partner_performance=round(partner_perf, 4),
            operational_efficiency=oper_eff,
            composite_score=round(composite_score, 2)
        )
