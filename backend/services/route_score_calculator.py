"""Stateless score calculator converting raw route operational parameters to standard 0-100 scores."""

from typing import Dict, Any
from backend.models.route_scoring_metrics import RouteScoreResult
from backend.utils.logger import logger


class RouteScoreCalculator:
    """Calculates normalized indices and composite business priorities for routing paths.

    Designed for reusability, modular weight systems, and dependency injection.
    """

    @classmethod
    def calculate_scores(
        cls,
        src: str,
        dest: str,
        distance: float,
        cost: float,
        transit_time: float,
        volume: float,
        capacity: float,
        partner_rating: float,
        sla_compliance: float
    ) -> RouteScoreResult:
        """Converts raw operational values to normalized scores (0 to 100) and aggregates composite indexes.

        Args:
            src: Source node ID.
            dest: Destination node ID.
            distance: Travel distance in miles.
            cost: Shipment cost.
            transit_time: Duration in days.
            volume: Shipment volume flow.
            capacity: Node capacity limit.
            partner_rating: Partner rating (1.0 to 5.0).
            sla_compliance: Historic SLA compliance % (0.0 to 100.0).

        Returns:
            RouteScoreResult: Set of computed metrics.
        """
        # 1. Normalize individual scoring dimensions to 0 - 100
        # Distance (longer -> lower score, benchmark 600 miles)
        dist_score = max(0.0, 100.0 * (1.0 - (distance / 600.0)))
        dist_score = min(100.0, dist_score)

        # Cost (higher -> lower score, benchmark $500)
        cost_score = max(0.0, 100.0 * (1.0 - (cost / 500.0)))
        cost_score = min(100.0, cost_score)

        # Transit Time (longer -> lower score, benchmark 5 days)
        time_score = max(0.0, 100.0 * (1.0 - (transit_time / 5.0)))
        time_score = min(100.0, time_score)

        # Capacity Utilization (optimal between 50% and 80%, overload penalties)
        util = (volume / capacity) if capacity > 0 else 0.5
        # Penalty is absolute distance from optimal 0.65 utilization
        cap_score = max(0.0, 100.0 * (1.0 - abs(util - 0.65) / 0.65))
        cap_score = min(100.0, cap_score)

        # SLA Compliance (direct mapping, default 100%)
        sla_val = sla_compliance if sla_compliance >= 0 else 100.0
        sla_score = min(100.0, max(0.0, sla_val))

        # Partner Reliability (5 stars scale -> 0 to 100 scale)
        rating_val = partner_rating if partner_rating >= 0 else 4.0
        reliability_score = min(100.0, max(0.0, rating_val * 20.0))

        # 2. Compute composite indices
        # Overall Route Score (weighted sum: 25% cost, 25% time, 15% SLA, 15% capacity, 10% distance, 10% partner)
        overall_score = (
            0.25 * cost_score +
            0.25 * time_score +
            0.15 * sla_score +
            0.15 * cap_score +
            0.10 * dist_score +
            0.10 * reliability_score
        )

        # Business Priority Score (high priority on speed and reliability: 40% time, 40% SLA, 20% partner)
        priority_score = (
            0.40 * time_score +
            0.40 * sla_score +
            0.20 * reliability_score
        )

        # Operational Risk Score (high risk when SLA is missed or capacity is overloaded)
        overload_penalty = 100.0 if util > 0.90 else (50.0 if util > 0.80 else 0.0)
        risk_score = 100.0 - (0.50 * sla_score + 0.50 * (100.0 - overload_penalty))
        risk_score = min(100.0, max(0.0, risk_score))

        # Cost Efficiency Score (high priority on cost: 80% cost, 20% distance)
        cost_eff = 0.80 * cost_score + 0.20 * dist_score

        # Performance Index (combines speed and SLA: 50% time, 50% SLA)
        perf_index = 0.50 * time_score + 0.50 * sla_score

        # Composite Logistics Score
        composite_score = overall_score

        return RouteScoreResult(
            route_id=f"{src} → {dest}",
            source=src,
            destination=dest,
            cost_score=round(cost_score, 2),
            transit_time_score=round(time_score, 2),
            capacity_score=round(cap_score, 2),
            sla_score=round(sla_score, 2),
            distance_score=round(dist_score, 2),
            partner_reliability_score=round(reliability_score, 2),
            overall_route_score=round(overall_score, 2),
            business_priority_score=round(priority_score, 2),
            operational_risk_score=round(risk_score, 2),
            performance_index=round(perf_index, 2),
            composite_logistics_score=round(composite_score, 2)
        )
