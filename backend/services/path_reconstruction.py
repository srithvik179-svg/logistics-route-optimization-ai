"""Path reconstruction helper for search algorithms."""

from typing import Dict, List, Any, Optional, Tuple
from backend.models.astar_result import AStarPathResult


class PathReconstructor:
    """Traces predecessor mappings and aggregates total distance, cost, transit times, and hops."""

    @classmethod
    def reconstruct(
        cls,
        predecessors: Dict[str, Optional[Tuple[str, float, float, float]]],
        source: str,
        destination: str,
        expansion_count: int,
        visited_count: int,
        explored_count: int,
        elapsed_ms: float
    ) -> AStarPathResult:
        """Reconstructs the AStarPathResult sequence and metrics.

        Args:
            predecessors: Maps node_id -> (parent_id, step_distance, step_cost, step_transit_time).
            source: Origin Node ID.
            destination: Destination Node ID.
            expansion_count: Number of node expansions.
            visited_count: Visited nodes count.
            explored_count: Explored nodes count.
            elapsed_ms: Execution duration.

        Returns:
            AStarPathResult payload.
        """
        # Reconstruct path nodes sequence
        path = []
        curr = destination
        
        # Accumulate edge stats
        tot_dist = 0.0
        tot_cost = 0.0
        tot_time = 0.0

        while curr is not None:
            path.append(curr)
            parent_info = predecessors.get(curr)
            if parent_info is not None:
                parent_id, dist, cost, time_val = parent_info
                tot_dist += dist
                tot_cost += cost
                tot_time += time_val
                curr = parent_id
            else:
                if curr != source:
                    # Broken path sequence (unreachable or missing parent)
                    return cls.empty_result(source, destination, elapsed_ms)
                curr = None

        path.reverse()

        return AStarPathResult(
            source=source,
            destination=destination,
            path_nodes=path,
            total_distance=round(tot_dist, 2),
            total_cost=round(tot_cost, 2),
            total_transit_time=round(tot_time, 2),
            hops=len(path) - 1,
            search_expansion_count=expansion_count,
            visited_nodes_count=visited_count,
            explored_nodes_count=explored_count,
            execution_time_ms=round(elapsed_ms, 4)
        )

    @classmethod
    def empty_result(
        cls,
        source: str,
        destination: str,
        elapsed_ms: float
    ) -> AStarPathResult:
        """Helper returning empty payload for unreachable paths."""
        return AStarPathResult(
            source=source,
            destination=destination,
            path_nodes=[],
            total_distance=999999.0,
            total_cost=999999.0,
            total_transit_time=999999.0,
            hops=0,
            search_expansion_count=0,
            visited_nodes_count=0,
            explored_nodes_count=0,
            execution_time_ms=round(elapsed_ms, 4)
        )
