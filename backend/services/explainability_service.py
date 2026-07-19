"""Explainability metadata service generating feature importance rankings and decision support feedback."""

from typing import Dict, Any, List
from backend.models.recommendation_candidate import RecommendationCandidate


class ExplainabilityService:
    """Compiles explainability summaries and confidence levels for recommendations."""

    @classmethod
    def generate_explainability_data(
        cls,
        candidates: List[RecommendationCandidate]
    ) -> Dict[str, Any]:
        """Compiles global explainability stats, feature importances, and algorithm scores comparisons.

        Args:
            candidates: Mapped recommendation options.

        Returns:
            Dict[str, Any]: Explainability metadata dictionary.
        """
        # Feature importances coefficients configurations
        feature_importances = {
            "transportation_cost": 0.40,
            "transit_time": 0.40,
            "sla_compliance": 0.10,
            "route_reliability": 0.05,
            "partner_performance": 0.05
        }

        # Compare algorithms
        algorithm_comparisons = {}
        for c in candidates:
            algorithm_comparisons[c.algorithm] = {
                "distance": c.distance,
                "cost": c.cost,
                "transit_time": c.transit_time,
                "confidence": c.confidence_score,
                "composite_score": c.composite_score
            }

        # Constraint safety buffer summary
        constraint_summary = {
            "max_transit_limit_days": 3.0,
            "feasibility_ratio": round(sum(1 for c in candidates if c.is_feasible) / len(candidates), 2) if candidates else 0.0
        }

        return {
            "feature_importance_weights": feature_importances,
            "algorithm_comparisons": algorithm_comparisons,
            "constraint_safety_summary": constraint_summary,
            "decision_confidence_index": 0.92 if constraint_summary["feasibility_ratio"] > 0.5 else 0.65
        }
