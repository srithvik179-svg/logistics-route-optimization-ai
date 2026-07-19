"""Heuristic computation service for geographic routing search algorithms."""

import math
import time
from typing import Dict, Tuple, Any
from backend.utils.logger import logger


class HeuristicService:
    """Calculates geographical heuristics between nodes.

    Supports Great-circle, Weighted, Transit-based, Cost-based, and Composite modes.
    Contains an internal cache to avoid repeating calculations.
    """

    def __init__(self, node_coords: Dict[str, Tuple[float, float]]) -> None:
        """Initializes the heuristic service with coordinates mapping.

        Args:
            node_coords: Dictionary mapping Node ID -> (latitude, longitude).
        """
        self._node_coords = node_coords
        self._distance_cache: Dict[Tuple[str, str], float] = {}
        self.computation_time_ms: float = 0.0
        self.cache_hits: int = 0

    def compute_heuristic(self, node_a: str, node_b: str, mode: str) -> float:
        """Main entry point for heuristic calculation.

        Args:
            node_a: Origin Node ID.
            node_b: Destination Node ID.
            mode: Heuristic mode: great-circle, weighted, transit, cost, composite.

        Returns:
            float: Heuristic estimate.
        """
        start_time = time.perf_counter()

        if node_a == node_b:
            return 0.0

        # Calculate or lookup Great-Circle Distance
        gc_dist = self._get_great_circle_distance(node_a, node_b)

        # Apply specific heuristic formulas
        if mode == "great-circle":
            val = gc_dist
        elif mode == "weighted":
            val = gc_dist * 1.25  # standard road distance correction factor
        elif mode == "transit":
            # Average transit velocity: 400 miles per day
            val = gc_dist / 400.0
        elif mode == "cost":
            # Average cost per mile: $0.50
            val = gc_dist * 0.50
        elif mode == "composite":
            # Composite = 80% cost heuristic + 20% transit heuristic
            cost_h = gc_dist * 0.50
            transit_h = gc_dist / 400.0
            val = 0.80 * cost_h + 0.20 * transit_h
        else:
            logger.warning(f"HeuristicService: Unsupported mode '{mode}'. Defaulting to great-circle.")
            val = gc_dist

        self.computation_time_ms += (time.perf_counter() - start_time) * 1000.0
        return round(val, 4)

    def _get_great_circle_distance(self, node_a: str, node_b: str) -> float:
        """Calculates great-circle distance between two node coordinates with cache lookup.

        Args:
            node_a: Node A ID.
            node_b: Node B ID.

        Returns:
            float: Distance in miles.
        """
        cache_key = tuple(sorted([node_a, node_b]))
        if cache_key in self._distance_cache:
            self.cache_hits += 1
            return self._distance_cache[cache_key]

        coord_a = self._node_coords.get(node_a)
        coord_b = self._node_coords.get(node_b)

        if not coord_a or not coord_b:
            # Fallback if coordinates are missing
            return 999.0

        lat1, lon1 = coord_a
        lat2, lon2 = coord_b

        # Haversine distance formula
        r = 3958.8  # Earth's radius in miles
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        
        a = math.sin(d_lat / 2.0) ** 2 + \
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
            math.sin(d_lon / 2.0) ** 2
        
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        distance = r * c

        self._distance_cache[cache_key] = distance
        return distance
