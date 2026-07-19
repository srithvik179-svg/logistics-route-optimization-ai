"""Search analytics and heuristic performance profiling services."""

import time
from typing import List, Dict, Any
from backend.models.astar_result import HeuristicMetrics
from backend.models.shortest_path_metrics import PathResult
from backend.services.heuristic_service import HeuristicService


class AStarStatistics:
    """Calculates search efficiency metrics and profiles heuristic deviations."""

    @classmethod
    def evaluate_heuristics_performance(
        cls,
        heur_service: HeuristicService,
        actual_paths: List[Any],
        mode: str
    ) -> HeuristicMetrics:
        """Compares heuristic estimates against actual computed weights to evaluate accuracy.

        Args:
            heur_service: Running HeuristicService instance.
            actual_paths: List of actual computed path results.
            mode: Active heuristic mode.

        Returns:
            HeuristicMetrics validation dataset.
        """
        errors = []

        for path in actual_paths:
            if not path or not path.path_nodes:
                continue

            src, dest = path.source, path.destination
            # Calculate heuristic estimate
            estimate = heur_service.compute_heuristic(src, dest, mode)

            # Actual cost metric depends on search weight (we assume distance for benchmark evaluation)
            actual = path.total_distance

            # Compute absolute error deviation
            errors.append(abs(estimate - actual))

        avg_error = sum(errors) / len(errors) if errors else 0.0

        return HeuristicMetrics(
            heuristic_type=mode,
            computation_time_ms=round(heur_service.computation_time_ms, 4),
            cache_hits=heur_service.cache_hits,
            average_error=round(avg_error, 2)
        )
