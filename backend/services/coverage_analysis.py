"""Geospatial network coverage and expansion opportunities analysis."""

import math
from typing import List, Dict, Tuple
from backend.models.geospatial_metrics import NetworkCoverageMetrics, NearestMapping
from backend.services.geospatial_service import GeospatialService
from backend.utils.logger import logger


class CoverageAnalysisService:
    """Analyzes network coverage holes, sparse nodes, high-density areas, and expansion opportunities.

    Stateless service designed for dependency injection.
    """

    @classmethod
    def analyze_coverage(
        cls,
        nearest_mappings: List[NearestMapping],
        node_coords: Dict[str, Tuple[float, float]]
    ) -> NetworkCoverageMetrics:
        """Evaluates proximity mappings to flag sparse networks, connectivity holes, and expansion recommendations.

        Args:
            nearest_mappings: List of computed nearest mappings.
            node_coords: Registered nodes.

        Returns:
            NetworkCoverageMetrics payload.
        """
        logger.info("CoverageAnalysisService: Running coverage analysis.")

        coverage = NetworkCoverageMetrics()

        if not nearest_mappings:
            return coverage

        # 1. Sparse & Highly Connected Areas checks
        for mapping in nearest_mappings:
            node_id = mapping.node_id
            dist_hub = mapping.distance_to_nearest_hub
            dist_rc = mapping.distance_to_nearest_repair_center

            # Distance to nearest node is proxy for density
            min_dist = min(dist_hub, dist_rc) if dist_hub > 0 and dist_rc > 0 else max(dist_hub, dist_rc)

            if min_dist > 300.0:
                coverage.sparse_areas.append(node_id)
            elif 0.0 < min_dist < 100.0:
                coverage.highly_connected_areas.append(node_id)

        # 2. Uncovered Regions & Low Connectivity Regions
        # Identify regions from active nodes
        active_regions = set()
        for node_id in node_coords.keys():
            reg = GeospatialService.COORDINATES_FALLBACK.get(node_id, {}).get("state") or "TX"
            active_regions.add(reg)

        # Predefined checklist of target states/regions
        target_regions = ["TX", "NM", "OK", "LA", "AR"]
        for target in target_regions:
            if target not in active_regions:
                coverage.uncovered_regions.append(target)

        # Low connectivity regions: active states that only have 1 node
        region_counts: Dict[str, int] = {}
        for node_id in node_coords.keys():
            reg = GeospatialService.COORDINATES_FALLBACK.get(node_id, {}).get("state") or "TX"
            region_counts[reg] = region_counts.get(reg, 0) + 1

        for reg, count in region_counts.items():
            if count <= 1:
                coverage.low_connectivity_regions.append(reg)

        # 3. Potential Expansion Regions (Recommended cities far from existing assets but high demand)
        # Predefined candidates with coordinates
        expansion_candidates = {
            "Lubbock": (33.5779, -101.8552),
            "McAllen": (26.2034, -98.2300),
            "Abilene": (32.4487, -99.7331)
        }

        for city, coords in expansion_candidates.items():
            # Check distance to nearest existing node
            min_dist = float("inf")
            for node_id, node_coords_val in node_coords.items():
                # Haversine distance helper (direct math to avoid circular dependencies)
                lat1, lon1 = coords
                lat2, lon2 = node_coords_val
                
                R = 3958.8
                phi1 = math_radians(lat1)
                phi2 = math_radians(lat2)
                d_phi = math_radians(lat2 - lat1)
                d_lambda = math_radians(lon2 - lon1)
                a = math_sin(d_phi / 2)**2 + math_cos(phi1) * math_cos(phi2) * math_sin(d_lambda / 2)**2
                c = 2 * math_atan2(math_sqrt(a), math_sqrt(1 - a))
                dist = R * c
                if dist < min_dist:
                    min_dist = dist

            # If city is > 150 miles from any node, it is an expansion candidate
            if min_dist > 150.0:
                coverage.potential_expansion_regions.append(f"{city} (Nearest node is {min_dist:.1f} miles)")

        logger.info("CoverageAnalysisService: Coverage Analysis Completed.")
        return coverage


# Math helper functions to keep service self-contained
def math_radians(x): return x * (3.141592653589793 / 180.0)
def math_sin(x): return math.sin(x)
def math_cos(x): return math.cos(x)
def math_sqrt(x): return math.sqrt(x)
def math_atan2(y, x): return math.atan2(y, x)
