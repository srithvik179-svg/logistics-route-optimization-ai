"""Route Graph Engine — Orchestrator with in-memory caching.

Primary entry point for route graph generation and topological analysis.
Serves as the weighted network foundation for pathfinding algorithms (Dijkstra, A*, etc.).
"""

import json
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime

from backend.services.repository import repository
from backend.services.geospatial_service import GeospatialService
from backend.services.graph_builder import GraphBuilder
from backend.services.graph_statistics import GraphStatistics
from backend.services.graph_analysis import GraphAnalysisService
from backend.models.graph_metrics import (
    GraphAnalyticsPayload,
    GraphOverviewStats,
    ConnectivityAnalysis,
)
from backend.utils.logger import logger


class GraphEngine:
    """Orchestrates route graph generation and topological network analytics.

    Responsibilities:
        1. Loads processed sheets from Repository.
        2. Configures node and edge structures using GraphBuilder.
        3. Coordinates statistics, adjacency networks, and connectivity breakdowns.
        4. Caches calculated graphs.
    """

    _cache: Dict[str, GraphAnalyticsPayload] = {}

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the in-memory cache."""
        cls._cache.clear()
        logger.info("GraphEngine: Cache cleared.")

    @classmethod
    def get_graph_payload(cls, filters: Dict[str, Any]) -> GraphAnalyticsPayload:
        """Main entry point returning a fully computed GraphAnalyticsPayload.

        Args:
            filters: Global filters dictionary.

        Returns:
            GraphAnalyticsPayload payload.
        """
        logger.info(f"GraphEngine: Graph Engine Started. Filters: {filters}")

        # --- Cache Lookup ---
        cache_key = cls._build_cache_key(filters)
        if cache_key in cls._cache:
            logger.info("GraphEngine: Cache HIT — returning cached payload.")
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
            logger.warning("GraphEngine: Empty dataset after filtering.")
            empty = cls._empty_payload(filters)
            cls._cache[cache_key] = empty
            return empty

        # --- 1. Nodes & Edges Generation ---
        nodes, edges = GraphBuilder.build_nodes_and_edges(df_filtered, df_hub, df_tpr)
        logger.info("GraphEngine: Nodes Generated.")
        logger.info("GraphEngine: Edges Generated.")

        # --- 2. Adjacency Structures ---
        adj_list, adj_matrix, neighbor_map, weighted_routes = GraphBuilder.construct_adjacency_structures(nodes, edges)

        # --- 3. Topology Statistics ---
        stats, components = GraphStatistics.compute_statistics(nodes, edges, adj_list)
        logger.info("GraphEngine: Graph Statistics Generated.")

        # --- 4. Connectivity Analysis ---
        connectivity = GraphAnalysisService.analyze_connectivity(nodes, edges, len(components))
        connectivity.disconnected_networks = components

        payload = GraphAnalyticsPayload(
            nodes=nodes,
            edges=edges,
            adjacency_list=adj_list,
            adjacency_matrix=adj_matrix,
            neighbor_mapping=neighbor_map,
            weighted_route_list=weighted_routes,
            statistics=stats,
            connectivity=connectivity,
            filters_applied=filters,
            cached=False
        )

        # Cache payload
        cls._cache[cache_key] = payload
        logger.info("GraphEngine: Graph Cached.")
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
    def _empty_payload(cls, filters: Dict[str, Any]) -> GraphAnalyticsPayload:
        return GraphAnalyticsPayload(
            nodes=[],
            edges=[],
            adjacency_list={},
            adjacency_matrix={},
            neighbor_mapping={},
            weighted_route_list=[],
            statistics=GraphOverviewStats(
                total_nodes=0, total_edges=0, avg_node_degree=0.0, max_degree=0,
                min_degree=0, connected_components=0, isolated_nodes=0,
                graph_density=0.0, avg_route_length=0.0
            ),
            connectivity=ConnectivityAnalysis(),
            filters_applied=filters,
            cached=False
        )
