"""Haversine distance calculator and proximity mapping engine."""

import math
from typing import Dict, List, Any, Tuple
from backend.models.geospatial_metrics import NearestMapping
from backend.services.geospatial_service import GeospatialService
from backend.utils.logger import logger


class DistanceCalculator:
    """Computes great-circle (Haversine) distances, road estimations, and proximity mappings.

    Stateless utility service designed for dependency injection.
    """

    @classmethod
    def haversine_distance(cls, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculates the great-circle distance in miles between two coordinate points.

        Args:
            lat1, lon1: Coordinates of first point.
            lat2, lon2: Coordinates of second point.

        Returns:
            float: Distance in miles.
        """
        # Earth radius in miles
        R = 3958.8
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        d_phi = math.radians(lat2 - lat1)
        d_lambda = math.radians(lon2 - lon1)

        a = math.sin(d_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c

    @classmethod
    def estimate_road_distance(cls, gc_distance: float) -> float:
        """Estimates actual road distance using circuity factor (nominal 1.25 multiplier)."""
        return gc_distance * 1.25

    @classmethod
    def build_distance_matrix(cls, node_coords: Dict[str, Tuple[float, float]]) -> Dict[str, Dict[str, float]]:
        """Constructs a complete N x N distance matrix mapping between all nodes.

        Args:
            node_coords: Dictionary mapping node_id to (lat, lon) coordinates tuple.

        Returns:
            Dict[str, Dict[str, float]]: Distance matrix dictionary of dictionaries.
        """
        logger.info("DistanceCalculator: Constructing distance matrix.")
        matrix: Dict[str, Dict[str, float]] = {}

        for n1, coords1 in node_coords.items():
            matrix[n1] = {}
            for n2, coords2 in node_coords.items():
                if n1 == n2:
                    matrix[n1][n2] = 0.0
                else:
                    matrix[n1][n2] = round(cls.haversine_distance(coords1[0], coords1[1], coords2[0], coords2[1]), 2)

        return matrix

    @classmethod
    def generate_nearest_mappings(
        cls,
        node_coords: Dict[str, Tuple[float, float]],
        matrix: Dict[str, Dict[str, float]]
    ) -> List[NearestMapping]:
        """Calculates nearest Hub, Warehouse, and Repair Center mappings for all nodes.

        Args:
            node_coords: Nodes registry.
            matrix: Pre-computed distance matrix.

        Returns:
            List[NearestMapping]: Proximity list.
        """
        logger.info("DistanceCalculator: Generating nearest node mappings.")
        mappings: List[NearestMapping] = []

        # Categorize node IDs based on fallbacks registry type
        hubs = []
        warehouses = []
        rcs = []

        for node_id in node_coords.keys():
            t = GeospatialService.COORDINATES_FALLBACK.get(node_id, {}).get("type", "Hub")
            if t == "Repair Center":
                rcs.append(node_id)
            elif t == "Warehouse":
                warehouses.append(node_id)
            else:
                hubs.append(node_id)

        # Fallback empty protections
        if not hubs:
            hubs = ["HUB-A"]
        if not warehouses:
            # If no warehouse sheet, use hubs as warehouse backup
            warehouses = hubs
        if not rcs:
            rcs = ["TPR-001"]

        for node_id in node_coords.keys():
            # 1. Find nearest Hub
            n_hub, d_hub = cls._find_nearest(node_id, hubs, matrix)
            # 2. Find nearest Warehouse
            n_wh, d_wh = cls._find_nearest(node_id, warehouses, matrix)
            # 3. Find nearest Repair Center
            n_rc, d_rc = cls._find_nearest(node_id, rcs, matrix)

            mappings.append(NearestMapping(
                node_id=node_id,
                nearest_hub=n_hub,
                distance_to_nearest_hub=round(d_hub, 2),
                nearest_warehouse=n_wh,
                distance_to_nearest_warehouse=round(d_wh, 2),
                nearest_repair_center=n_rc,
                distance_to_nearest_repair_center=round(d_rc, 2)
            ))

        return mappings

    @classmethod
    def _find_nearest(cls, node_id: str, candidates: List[str], matrix: Dict[str, Dict[str, float]]) -> Tuple[str, float]:
        min_dist = float("inf")
        nearest = "Unknown"

        for cand in candidates:
            if cand == node_id:
                # Proximity search excludes self
                continue
            dist = matrix.get(node_id, {}).get(cand, float("inf"))
            if dist < min_dist:
                min_dist = dist
                nearest = cand

        if min_dist == float("inf"):
            # Fallback if no neighbors
            min_dist = 0.0
            nearest = node_id

        return nearest, min_dist
