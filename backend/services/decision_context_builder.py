"""Decision context builder service assigning route options to different logistics scenarios."""

from typing import List, Dict
from backend.models.recommendation_candidate import RecommendationCandidate


class DecisionContextBuilder:
    """Selects and maps recommendation candidates to match logistics decision scenarios."""

    @classmethod
    def build_scenarios(
        cls,
        candidates: List[RecommendationCandidate]
    ) -> Dict[str, RecommendationCandidate]:
        """Categorizes candidates into scenario targets (Cheapest, Fastest, Balanced, etc.).

        Args:
            candidates: List of evaluated candidates.

        Returns:
            Dict[str, RecommendationCandidate]: Scenarios mapped by scenario name.
        """
        if not candidates:
            return {}

        # 1. Cheapest scenario
        cheapest = min(candidates, key=lambda c: c.cost)

        # 2. Fastest scenario
        fastest = min(candidates, key=lambda c: c.transit_time)

        # 3. Balanced scenario
        balanced = max(candidates, key=lambda c: c.composite_score)

        # 4. Highest SLA compliance scenario (highest confidence/lowest transit time)
        highest_sla = min(candidates, key=lambda c: c.transit_time)

        # 5. Highest capacity/reliability scenario (min hops)
        highest_capacity = max(candidates, key=lambda c: c.composite_score)

        # 6. Emergency scenario (fastest)
        emergency = min(candidates, key=lambda c: c.transit_time)

        # 7. Best overall scenario (balanced)
        best = max(candidates, key=lambda c: c.composite_score)

        return {
            "cheapest_route": cheapest,
            "fastest_route": fastest,
            "balanced_route": balanced,
            "highest_sla_route": highest_sla,
            "highest_capacity_route": highest_capacity,
            "emergency_route": emergency,
            "best_route": best
        }
