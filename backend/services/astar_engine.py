"""A* Pathfinding Engine — Orchestrator with in-memory caching.

Primary routing engine designed for efficient optimal path calculations using graph topology
and geographic coordinate-based heuristics.
"""

import json
import time
from typing import Dict, Any, List, Optional, Tuple

from backend.services.graph_engine import GraphEngine
from backend.services.priority_queue import AStarPriorityQueue
from backend.services.heuristic_service import HeuristicService
from backend.services.path_reconstruction import PathReconstructor
from backend.services.astar_statistics import AStarStatistics
from backend.models.astar_result import AStarPayload, AStarPathResult, HeuristicMetrics
from backend.utils.logger import logger


class AStarEngine:
    """Computes optimal route sequences using geographical heuristics and graph structures.

    Responsibilities:
        1. Loads graph models from Route Graph Engine.
        2. Computes A* optimal paths for single or multiple destinations.
        3. Supports multiple geographical heuristics.
        4. Compiles performance profiles and accuracy checks.
        5. Caches calculations.
    """

    _cache: Dict[str, AStarPayload] = {}

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the in-memory cache."""
        cls._cache.clear()
        logger.info("A* Cache Updated: cache cleared.")

    @classmethod
    def get_astar_payload(
        cls,
        filters: Dict[str, Any],
        heuristic_type: str = "great-circle"
    ) -> AStarPayload:
        """Main entry point returning a fully precalculated A* Pathfinding Payload.

        Computes all-pairs optimal paths to populate the reusable dataset.

        Args:
            filters: Global filters dictionary.
            heuristic_type: Active heuristic type.

        Returns:
            AStarPayload payload.
        """
        logger.info("A* Engine Started.")

        # --- Cache Lookup ---
        cache_key = cls._build_cache_key(filters, heuristic_type)
        if cache_key in cls._cache:
            logger.info("A* Cache Updated: cache hit returned.")
            cached = cls._cache[cache_key]
            cached.cached = True
            return cached

        # --- Load graph ---
        graph = GraphEngine.get_graph_payload(filters)
        nodes = [n.node_id for n in graph.nodes]
        coords = {n.node_id: (n.latitude, n.longitude) for n in graph.nodes}
        neighbor_map = graph.neighbor_mapping

        if not nodes:
            logger.warning("A* Pathfinding Engine: Empty graph registry.")
            empty = cls._empty_payload(filters)
            cls._cache[cache_key] = empty
            return empty

        # Initialize heuristic service
        heur_service = HeuristicService(coords)
        logger.info("Heuristic Generated.")

        paths: Dict[str, Dict[str, AStarPathResult]] = {}
        all_results = []
        start_run = time.perf_counter()

        # All-Pairs A* Search computation
        for src in nodes:
            paths[src] = {}
            for dest in nodes:
                if src == dest:
                    continue

                path_res = cls.find_path(
                    nodes, coords, neighbor_map, src, dest, heuristic_type, heur_service
                )
                if path_res and path_res.path_nodes:
                    paths[src][dest] = path_res
                    all_results.append(path_res)

        elapsed_run_ms = (time.perf_counter() - start_run) * 1000.0
        logger.info("Optimal Path Found.")

        # --- Search Statistics ---
        expansions = sum(r.search_expansion_count for r in all_results)
        visited = sum(r.visited_nodes_count for r in all_results)
        explored = sum(r.explored_nodes_count for r in all_results)

        search_stats = {
            "total_expansions": expansions,
            "total_visited": visited,
            "total_explored": explored,
            "overall_execution_time_ms": round(elapsed_run_ms, 2),
            "average_path_distance": round(sum(r.total_distance for r in all_results) / len(all_results), 2) if all_results else 0.0,
            "average_path_cost": round(sum(r.total_cost for r in all_results) / len(all_results), 2) if all_results else 0.0,
            "average_path_time": round(sum(r.total_transit_time for r in all_results) / len(all_results), 2) if all_results else 0.0
        }
        logger.info("Search Statistics Generated.")

        # Heuristic Accuracy & Errors analysis
        heur_metrics = AStarStatistics.evaluate_heuristics_performance(
            heur_service, all_results, heuristic_type
        )

        metadata = {
            "nodes_evaluated": len(nodes),
            "paths_calculated": len(all_results),
            "heuristic_selected": heuristic_type
        }

        payload = AStarPayload(
            paths=paths,
            heuristics_performance=[heur_metrics],
            search_statistics=search_stats,
            metadata=metadata,
            filters_applied=filters,
            cached=False
        )

        cls._cache[cache_key] = payload
        logger.info("A* Cache Updated: cache updated.")
        return payload

    @classmethod
    def find_path(
        cls,
        nodes: List[str],
        coords: Dict[str, Tuple[float, float]],
        neighbor_map: Dict[str, List[Dict[str, Any]]],
        source: str,
        destination: str,
        heuristic_type: str,
        heur_service: Optional[HeuristicService] = None
    ) -> Optional[AStarPathResult]:
        """Calculates optimal path between source and destination using A* search.

        Args:
            nodes: Nodes list.
            coords: Node coordinates dict mapping Node ID -> (lat, lon).
            neighbor_map: Graph adjacency map detailing neighbor edges attributes.
            source: Origin Node ID.
            destination: Destination Node ID.
            heuristic_type: Heuristic function mode to use.
            heur_service: Pre-instantiated HeuristicService (optional).

        Returns:
            Optional[AStarPathResult]: Optimal route result if path exists, else None.
        """
        start_time = time.perf_counter()

        if source not in neighbor_map or destination not in neighbor_map:
            logger.warning(f"A* Pathfinding warning: Source '{source}' or Destination '{destination}' not in graph.")
            return PathReconstructor.empty_result(source, destination, 0.0)

        if heur_service is None:
            heur_service = HeuristicService(coords)

        # Distances from source to node (g score)
        g_scores: Dict[str, float] = {n: float("inf") for n in nodes}
        g_scores[source] = 0.0

        # Predecessors map: node -> (parent, distance, cost, transit_time)
        predecessors: Dict[str, Optional[Tuple[str, float, float, float]]] = {source: None}

        # Initialize priority queue
        pq = AStarPriorityQueue()
        h_score = heur_service.compute_heuristic(source, destination, heuristic_type)
        pq.push(source, 0.0 + h_score)

        visited_nodes = set()
        explored_nodes = {source}
        expansions = 0

        while not pq.is_empty():
            curr_f, curr_node = pq.pop()

            if curr_node == destination:
                break

            if curr_node in visited_nodes:
                continue

            visited_nodes.add(curr_node)
            expansions += 1

            for edge in neighbor_map.get(curr_node, []):
                neigh = edge["destination"]
                # Default weight is route distance
                edge_weight = float(edge.get("distance", 999.0))
                tentative_g = g_scores[curr_node] + edge_weight

                if tentative_g < g_scores[neigh]:
                    predecessors[neigh] = (
                        curr_node,
                        edge.get("distance", 0.0),
                        edge.get("cost", 0.0),
                        edge.get("transit_time", 0.0)
                    )
                    g_scores[neigh] = tentative_g
                    explored_nodes.add(neigh)
                    
                    h = heur_service.compute_heuristic(neigh, destination, heuristic_type)
                    pq.push(neigh, tentative_g + h)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Reconstruct path stats
        if g_scores[destination] == float("inf"):
            logger.warning(f"A* Pathfinding warning: No valid route exists from '{source}' to '{destination}'.")
            return PathReconstructor.empty_result(source, destination, elapsed_ms)

        return PathReconstructor.reconstruct(
            predecessors,
            source,
            destination,
            expansions,
            len(visited_nodes),
            len(explored_nodes),
            elapsed_ms
        )

    # ────────────────────────────────────────────
    # Private Helpers
    # ────────────────────────────────────────────

    @classmethod
    def _build_cache_key(cls, filters: Dict[str, Any], heuristic_type: str) -> str:
        sorted_items = sorted(
            ((k, v) for k, v in filters.items() if v),
            key=lambda x: x[0]
        )
        return json.dumps((sorted_items, heuristic_type), default=str)

    @classmethod
    def _empty_payload(cls, filters: Dict[str, Any]) -> AStarPayload:
        return AStarPayload(
            paths={},
            heuristics_performance=[],
            search_statistics={},
            metadata={},
            filters_applied=filters,
            cached=False
        )
