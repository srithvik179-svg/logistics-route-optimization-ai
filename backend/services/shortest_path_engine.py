"""Shortest Path Analytics Engine — Orchestrator with in-memory caching.

Primary entry point for routing optimizations. Coordinates Dijkstra, BFS,
and DFS algorithms to evaluate path sequences, accessibility, and traversal performance.
"""

import json
import time
from typing import Dict, Any, List
from datetime import datetime

from backend.services.graph_engine import GraphEngine
from backend.services.dijkstra_service import DijkstraService
from backend.services.traversal_services import TraversalService
from backend.models.shortest_path_metrics import (
    ShortestPathPayload,
    ShortestPathOverviewStats,
    NetworkAccessibility,
    PathResult,
)
from backend.utils.logger import logger


class ShortestPathEngine:
    """Orchestrates shortest path traversal computations across all nodes.

    Responsibilities:
        1. Loads graph representations from GraphEngine.
        2. Computes all-pairs Dijkstra routing pathways.
        3. Invokes BFS and DFS benchmarks.
        4. Calculates topological accessibility and performance statistics.
        5. Caches calculated paths.
    """

    _cache: Dict[str, ShortestPathPayload] = {}

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the in-memory cache."""
        cls._cache.clear()
        logger.info("ShortestPathEngine: Cache cleared.")

    @classmethod
    def get_shortest_path_payload(cls, filters: Dict[str, Any]) -> ShortestPathPayload:
        """Main entry point returning a fully computed ShortestPathPayload.

        Args:
            filters: Global filters dictionary.

        Returns:
            ShortestPathPayload payload.
        """
        logger.info(f"ShortestPathEngine: Shortest Path Engine Started. Filters: {filters}")

        # --- Cache Lookup ---
        cache_key = cls._build_cache_key(filters)
        if cache_key in cls._cache:
            logger.info("ShortestPathEngine: Cache HIT — returning cached payload.")
            cached = cls._cache[cache_key]
            cached.cached = True
            return cached

        # --- Load graph payload ---
        graph = GraphEngine.get_graph_payload(filters)
        nodes = [n.node_id for n in graph.nodes]
        neighbor_map = graph.neighbor_mapping

        if not nodes:
            logger.warning("ShortestPathEngine: Empty graph registry.")
            empty = cls._empty_payload(filters)
            cls._cache[cache_key] = empty
            return empty

        # Benchmark search performance
        start_time = time.perf_counter()

        # Weight function (shortest distance)
        dist_weight = lambda edge: float(edge.get("distance", 0.0))

        shortest_paths: Dict[str, Dict[str, PathResult]] = {}
        path_lengths = []
        calculations_count = 0

        # Dijkstra All-Pairs calculation
        for src in nodes:
            shortest_paths[src] = {}
            for dest in nodes:
                if src == dest:
                    continue
                
                path_res = DijkstraService.find_shortest_path(nodes, neighbor_map, src, dest, dist_weight)
                if path_res:
                    shortest_paths[src][dest] = path_res
                    path_lengths.append(len(path_res.path_nodes))
                    calculations_count += 1

        logger.info("ShortestPathEngine: Dijkstra Completed.")

        # BFS & DFS Log triggers for performance validation audits
        cls._run_bfs_dfs_verification(nodes, neighbor_map)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        avg_search_time = elapsed_ms / calculations_count if calculations_count > 0 else 0.0

        # --- Statistics ---
        stats = ShortestPathOverviewStats(
            average_search_time_ms=round(avg_search_time, 4),
            average_path_length=round(sum(path_lengths) / len(path_lengths), 2) if path_lengths else 0.0,
            max_path_length=max(path_lengths) if path_lengths else 0,
            min_path_length=min(path_lengths) if path_lengths else 0,
            total_calculations=calculations_count
        )

        # --- Accessibility (delegated) ---
        reachable, unreachable, highly_acc, least_acc = TraversalService.compute_accessibility(nodes, neighbor_map)
        
        accessibility = NetworkAccessibility(
            reachable_nodes=reachable,
            unreachable_nodes=unreachable,
            highly_accessible_hubs=highly_acc,
            least_accessible_hubs=least_acc
        )

        payload = ShortestPathPayload(
            shortest_paths=shortest_paths,
            statistics=stats,
            accessibility=accessibility,
            filters_applied=filters,
            cached=False
        )

        # Cache payload
        cls._cache[cache_key] = payload
        logger.info("ShortestPathEngine: Path Cache Updated.")
        return payload

    # ────────────────────────────────────────────
    # Private Helpers
    # ────────────────────────────────────────────

    @classmethod
    def _build_cache_key(cls, filters: Dict[str, Any]) -> str:
        sorted_items = sorted(
            ((k, v) for k, v in filters.items() if v),
            key=lambda x: x[0]
        )
        return json.dumps(sorted_items, default=str)

    @classmethod
    def _run_bfs_dfs_verification(cls, nodes: List[str], neighbor_map: Dict[str, List[Dict[str, Any]]]) -> None:
        """Executes lightweight sample traversals to confirm BFS & DFS function."""
        if len(nodes) < 2:
            return

        src, dest = nodes[0], nodes[-1]
        TraversalService.find_path_bfs(neighbor_map, src, dest)
        logger.info("ShortestPathEngine: BFS Completed.")

        TraversalService.find_path_dfs(neighbor_map, src, dest)
        logger.info("ShortestPathEngine: DFS Completed.")

    @classmethod
    def _empty_payload(cls, filters: Dict[str, Any]) -> ShortestPathPayload:
        return ShortestPathPayload(
            shortest_paths={},
            statistics=ShortestPathOverviewStats(
                average_search_time_ms=0.0, average_path_length=0.0,
                max_path_length=0, min_path_length=0, total_calculations=0
            ),
            accessibility=NetworkAccessibility(),
            filters_applied=filters,
            cached=False
        )
