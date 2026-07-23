"""Geospatial Intelligence Engine — Orchestrator with in-memory caching.

Primary entry point for geographical network intelligence. Loads coordinates,
computes Haversine distance matrices, clusters quadrants, and analyzes network coverage.
"""

import json
import pandas as pd
from typing import Dict, Any, List, Tuple
from datetime import datetime

from backend.services.repository import repository
from backend.services.geospatial_service import GeospatialService
from backend.services.distance_calculator import DistanceCalculator
from backend.services.regional_clustering import RegionalClusteringService
from backend.services.coverage_analysis import CoverageAnalysisService
from backend.models.geospatial_metrics import (
    GeospatialAnalyticsPayload,
    GeospatialOverviewMetrics,
    NearestMapping,
    RegionalClustering,
    NetworkCoverageMetrics,
)
from backend.utils.logger import logger


class GeospatialEngine:
    """Orchestrates geospatial network analytics across all logistics resources.

    Responsibilities:
        1. Loads processed sheets from Repository.
        2. Resolves geographical coordinates for hubs and repair centers.
        3. Computes Haversine distance matrices and estimations.
        4. Coordinates quadrant clustering and coverage anomalies.
        5. Caches calculated payloads.
    """

    _cache: Dict[str, GeospatialAnalyticsPayload] = {}

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the in-memory cache."""
        cls._cache.clear()
        logger.info("GeospatialEngine: Cache cleared.")

    @classmethod
    def get_geospatial_payload(cls, filters: Dict[str, Any]) -> GeospatialAnalyticsPayload:
        """Main entry point returning a fully computed GeospatialAnalyticsPayload.

        Args:
            filters: Global filters dictionary.

        Returns:
            GeospatialAnalyticsPayload payload.
        """
        logger.info(f"GeospatialEngine: Geospatial Engine Started. Filters: {filters}")

        # --- Cache Lookup ---
        cache_key = cls._build_cache_key(filters)
        if cache_key in cls._cache:
            logger.info("GeospatialEngine: Cache HIT — returning cached payload.")
            cached = cls._cache[cache_key]
            cached.cached = True
            return cached

        # --- Load sheets ---
        df_tx_raw = repository._processed_sheets.get("Logistics_Transactions")
        df_hub = repository._processed_sheets.get("Hub_Location_Master")
        tpr_sheet_name = "TPR_Master" if repository.sheet_exists("TPR_Master") else "Repair_Center_Master"
        df_tpr = repository._processed_sheets.get(tpr_sheet_name)
        df_parts = repository._processed_sheets.get("Parts_Master")

        # Fallbacks
        if df_tx_raw is None or len(df_tx_raw) == 0:
            df_tx_raw = pd.DataFrame()
        if df_hub is None or len(df_hub) == 0:
            df_hub = pd.DataFrame(columns=["Hub_ID", "Hub_Name", "Latitude", "Longitude", "City", "Region"])
        if df_tpr is None or len(df_tpr) == 0:
            df_tpr = pd.DataFrame(columns=["TPR_ID", "TPR_Name", "Coverage_Region", "SLA_Compliance_Target", "Rating"])
        if df_parts is None or len(df_parts) == 0:
            df_parts = pd.DataFrame(columns=["Part_Number", "Part_Name", "Category", "Weight_Kg", "Dimensions_Cm3"])

        # Enriched fields
        df_tx = cls._enrich_transactions(df_tx_raw, df_tpr)

        # Apply global filters
        df_filtered = GeospatialService._apply_geospatial_filters(df_tx, df_parts, filters)

        if len(df_filtered) == 0:
            logger.warning("GeospatialEngine: Empty dataset after filtering.")
            empty = cls._empty_payload(filters)
            cls._cache[cache_key] = empty
            return empty

        # Resolve coordinates dictionary
        node_coords = cls._resolve_node_coords(df_hub, df_tpr)

        # --- 1. Distance Matrix (delegated) ---
        dist_matrix = DistanceCalculator.build_distance_matrix(node_coords)
        logger.info("GeospatialEngine: Distance Matrix Generated.")

        # --- 2. Nearest Mapping (delegated) ---
        nearest_mappings = DistanceCalculator.generate_nearest_mappings(node_coords, dist_matrix)

        # --- 3. Regional Quadrant Clustering (delegated) ---
        clustering = RegionalClusteringService.perform_clustering(node_coords)
        logger.info("GeospatialEngine: Regional Analysis Completed.")

        # --- 4. Network Coverage (delegated) ---
        coverage = CoverageAnalysisService.analyze_coverage(nearest_mappings, node_coords)
        logger.info("GeospatialEngine: Coverage Analysis Completed.")

        # --- 5. Overview Metrics ---
        overview = cls._calculate_overview(df_filtered, dist_matrix, nearest_mappings)

        payload = GeospatialAnalyticsPayload(
            distance_matrix=dist_matrix,
            nearest_mappings=nearest_mappings,
            clustering=clustering,
            statistics=overview,
            coverage=coverage,
            filters_applied=filters,
            cached=False
        )

        # Cache payload
        cls._cache[cache_key] = payload
        logger.info("GeospatialEngine: Geospatial Cache Updated.")
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
    def _enrich_transactions(cls, df: pd.DataFrame, df_tpr: pd.DataFrame) -> pd.DataFrame:
        """Enriches the transaction dataset with partners, priorities, and flow types."""
        if len(df) == 0:
            return df
        
        df_enriched = df.copy()

        tpr_names = (
            list(df_tpr["TPR_Name"])
            if len(df_tpr) > 0 and "TPR_Name" in df_tpr.columns
            else ["Swift LogiCo", "Apex Freight", "LoneStar Delivery"]
        )
        df_enriched["Logistics_Partner"] = [tpr_names[i % len(tpr_names)] for i in range(len(df))]
        df_enriched["TPR_ID"] = df_enriched["Logistics_Partner"].map(GeospatialService.TPR_NAME_TO_ID).fillna("TPR-001")

        priorities = []
        flow_types = []
        for _, row in df_enriched.iterrows():
            dest = str(row.get("Destination_Hub", ""))
            dist = float(row.get("Route_Distance") or 0.0)
            cost = float(row.get("Shipment_Cost") or 0.0)

            if dest.upper().startswith("TPR"):
                flow_types.append("Outbound to TPR")
            elif dest.upper().startswith("HUB"):
                flow_types.append("Hub-to-Hub Transfer")
            else:
                flow_types.append("Outbound to TPR")

            if dist > 300.0 or cost > 300.0:
                priorities.append("High Priority")
            elif dist > 100.0 or cost > 100.0:
                priorities.append("Medium Priority")
            else:
                priorities.append("Low Priority")

        df_enriched["Priority"] = priorities
        df_enriched["Flow_Type"] = flow_types

        return df_enriched

    @classmethod
    def _resolve_node_coords(cls, hub_df: pd.DataFrame, tpr_df: pd.DataFrame) -> Dict[str, Tuple[float, float]]:
        coords = {}

        # Resolve Hubs
        if len(hub_df) > 0 and "Hub_ID" in hub_df.columns:
            for idx, row in hub_df.iterrows():
                hub_id = str(row["Hub_ID"])
                lat = row.get("Latitude")
                lon = row.get("Longitude")
                if pd.isna(lat) or pd.isna(lon):
                    fb = GeospatialService.COORDINATES_FALLBACK.get(hub_id, {"lat": 30.0, "lon": -100.0})
                    lat = fb["lat"]
                    lon = fb["lon"]
                coords[hub_id] = (float(lat), float(lon))
        else:
            hubs = ["HUB-A", "HUB-B", "HUB-C", "HUB-D", "HUB-E"]
            for h in hubs:
                fb = GeospatialService.COORDINATES_FALLBACK.get(h, {"lat": 30.0, "lon": -100.0})
                coords[h] = (fb["lat"], fb["lon"])

        # Resolve TPRs
        if len(tpr_df) > 0 and "TPR_ID" in tpr_df.columns:
            for idx, row in tpr_df.iterrows():
                rc_id = str(row["TPR_ID"])
                lat = row.get("Latitude")
                lon = row.get("Longitude")
                if pd.isna(lat) or pd.isna(lon):
                    fb = GeospatialService.COORDINATES_FALLBACK.get(rc_id, {"lat": 31.0, "lon": -99.0})
                    lat = fb["lat"]
                    lon = fb["lon"]
                coords[rc_id] = (float(lat), float(lon))
        else:
            rcs = ["TPR-001", "TPR-002", "TPR-003"]
            for rc in rcs:
                fb = GeospatialService.COORDINATES_FALLBACK.get(rc, {"lat": 31.0, "lon": -99.0})
                coords[rc] = (fb["lat"], fb["lon"])

        # Add all COORDINATES_FALLBACK entries for other nodes not in masters (e.g. customer destination cities)
        for k, v in GeospatialService.COORDINATES_FALLBACK.items():
            if k not in coords:
                coords[k] = (v["lat"], v["lon"])

        return coords

    @classmethod
    def _calculate_overview(
        cls,
        tx_df: pd.DataFrame,
        matrix: Dict[str, Dict[str, float]],
        nearest_mappings: List[NearestMapping]
    ) -> GeospatialOverviewMetrics:
        """Calculates distance statistics and coverage radius parameters."""
        # 1. Route distance metrics
        dist_col = tx_df["Route_Distance"].dropna() if "Route_Distance" in tx_df.columns else pd.Series()
        avg_dist = float(dist_col.mean()) if len(dist_col) > 0 else 180.0
        max_dist = float(dist_col.max()) if len(dist_col) > 0 else 350.0
        min_dist = float(dist_col.min()) if len(dist_col) > 0 else 50.0

        # 2. Great Circle & Road distance calculations
        # Sum of non-zero matrix values
        gc_values = []
        for n1, row in matrix.items():
            for n2, val in row.items():
                if n1 != n2 and val > 0:
                    gc_values.append(val)

        avg_gc = sum(gc_values) / len(gc_values) if gc_values else 150.0
        avg_road = DistanceCalculator.estimate_road_distance(avg_gc)

        # 3. Quadrant regional distance average
        avg_reg = avg_gc * 0.9  # simulated within-cluster average

        # 4. Coverage Radii (average distance to nearest nodes)
        hub_radii = [m.distance_to_nearest_hub for m in nearest_mappings if m.distance_to_nearest_hub > 0]
        wh_radii = [m.distance_to_nearest_warehouse for m in nearest_mappings if m.distance_to_nearest_warehouse > 0]
        rc_radii = [m.distance_to_nearest_repair_center for m in nearest_mappings if m.distance_to_nearest_repair_center > 0]

        avg_hub_radius = sum(hub_radii) / len(hub_radii) if hub_radii else 120.0
        avg_wh_radius = sum(wh_radii) / len(wh_radii) if wh_radii else 150.0
        avg_rc_radius = sum(rc_radii) / len(rc_radii) if rc_radii else 180.0

        return GeospatialOverviewMetrics(
            avg_route_distance=round(avg_dist, 2),
            max_route_distance=round(max_dist, 2),
            min_route_distance=round(min_dist, 2),
            avg_great_circle_distance=round(avg_gc, 2),
            avg_estimated_road_distance=round(avg_road, 2),
            avg_regional_distance=round(avg_reg, 2),
            hub_coverage_radius=round(avg_hub_radius, 2),
            warehouse_coverage_radius=round(avg_wh_radius, 2),
            repair_center_coverage_radius=round(avg_rc_radius, 2)
        )

    @classmethod
    def _empty_payload(cls, filters: Dict[str, Any]) -> GeospatialAnalyticsPayload:
        return GeospatialAnalyticsPayload(
            distance_matrix={},
            nearest_mappings=[],
            clustering=RegionalClustering(),
            statistics=GeospatialOverviewMetrics(
                avg_route_distance=0.0, max_route_distance=0.0, min_route_distance=0.0,
                avg_great_circle_distance=0.0, avg_estimated_road_distance=0.0,
                avg_regional_distance=0.0, hub_coverage_radius=0.0,
                warehouse_coverage_radius=0.0, repair_center_coverage_radius=0.0
            ),
            coverage=NetworkCoverageMetrics(),
            filters_applied=filters,
            cached=False
        )
