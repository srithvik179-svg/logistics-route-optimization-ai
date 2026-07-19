"""Dijkstra shortest path algorithm implementation for weighted networks."""

import heapq
from typing import Dict, List, Any, Tuple, Optional, Callable
from backend.models.shortest_path_metrics import PathResult
from backend.models.graph_metrics import GraphNode, GraphEdge
from backend.utils.logger import logger


class DijkstraService:
    """Computes shortest path routing sequences using Dijkstra's algorithm.

    Designed for reusability, modular weight functions, and dependency injection.
    """

    @classmethod
    def find_shortest_path(
        cls,
        nodes: List[str],
        neighbor_map: Dict[str, List[Dict[str, Any]]],
        source: str,
        destination: str,
        weight_fn: Callable[[Dict[str, Any]], float]
    ) -> Optional[PathResult]:
        """Calculates the single-source shortest path using Dijkstra's algorithm.

        Args:
            nodes: List of all node IDs in the graph.
            neighbor_map: Adjacency map detailing neighbors and edge attributes.
            source: Source node ID.
            destination: Destination node ID.
            weight_fn: Lambda or function returning the target weight of an edge dictionary.

        Returns:
            Optional[PathResult]: Shortest path result if path exists, else None.
        """
        if source not in neighbor_map or destination not in neighbor_map:
            return None

        # distances[node] = (min_weight, predecessor_id, accum_distance, accum_cost, accum_time)
        distances: Dict[str, Tuple[float, Optional[str], float, float, float]] = {
            n: (float("inf"), None, 0.0, 0.0, 0.0) for n in nodes
        }
        distances[source] = (0.0, None, 0.0, 0.0, 0.0)

        # Min-heap stores: (weight, node_id)
        pq: List[Tuple[float, str]] = [(0.0, source)]

        while pq:
            curr_weight, curr_node = heapq.heappop(pq)

            # Destination optimization
            if curr_node == destination:
                break

            # Skip outdated entries
            if curr_weight > distances[curr_node][0]:
                continue

            for edge in neighbor_map.get(curr_node, []):
                neigh = edge["destination"]
                weight_val = weight_fn(edge)
                new_weight = curr_weight + weight_val

                if new_weight < distances[neigh][0]:
                    # Accumulate path cost parameters
                    prev_stats = distances[curr_node]
                    distances[neigh] = (
                        new_weight,
                        curr_node,
                        prev_stats[2] + edge.get("distance", 0.0),
                        prev_stats[3] + edge.get("cost", 0.0),
                        prev_stats[4] + edge.get("transit_time", 0.0)
                    )
                    heapq.heappush(pq, (new_weight, neigh))

        # Check if unreachable
        if distances[destination][0] == float("inf"):
            return None

        # Reconstruct path sequence
        path = []
        curr = destination
        while curr is not None:
            path.append(curr)
            curr = distances[curr][1]
        path.reverse()

        stats = distances[destination]
        return PathResult(
            source=source,
            destination=destination,
            path_nodes=path,
            total_distance=round(stats[2], 2),
            total_cost=round(stats[3], 2),
            total_transit_time=round(stats[4], 2),
            hops=len(path) - 1
        )
