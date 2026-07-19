"""Logistics network route graph builder from transaction and master datasets."""

import pandas as pd
from typing import List, Dict, Any, Tuple

from backend.services.geospatial_service import GeospatialService
from backend.models.graph_metrics import GraphNode, GraphEdge, WeightedRouteEntry
from backend.utils.logger import logger


class GraphBuilder:
    """Builds node and edge entities and adjacency structures from logistics datasets.

    Designed for reusability and dependency injection.
    """

    @classmethod
    def build_nodes_and_edges(
        cls,
        tx_df: pd.DataFrame,
        hub_df: pd.DataFrame,
        tpr_df: pd.DataFrame
    ) -> Tuple[List[GraphNode], List[GraphEdge]]:
        """Identifies nodes and aggregates operational edge weights from transaction history.

        Args:
            tx_df: Transactions DataFrame.
            hub_df: Hub master DataFrame.
            tpr_df: TPR master DataFrame.

        Returns:
            Tuple[List[GraphNode], List[GraphEdge]]: Built node and edge objects lists.
        """
        logger.info("GraphBuilder: Building graph nodes and edges.")

        # --- 1. Nodes Generation ---
        nodes: List[GraphNode] = []
        hubs = list(hub_df["Hub_ID"].unique()) if len(hub_df) > 0 else ["HUB-A", "HUB-B", "HUB-C", "HUB-D", "HUB-E"]
        rcs = list(tpr_df["TPR_ID"].unique()) if len(tpr_df) > 0 else ["TPR-001", "TPR-002", "TPR-003"]

        # Hub Nodes
        for h in hubs:
            fb = GeospatialService.COORDINATES_FALLBACK.get(h, {})
            nodes.append(GraphNode(
                node_id=h,
                name=fb.get("city", f"Hub {h}") + " Logistics Hub",
                node_type="Hub",
                latitude=fb.get("lat", 30.0),
                longitude=fb.get("lon", -100.0),
                region=fb.get("state", "TX"),
                city=fb.get("city", "Unknown"),
                capacity=fb.get("capacity", 5000.0)
            ))

        # Repair Center Nodes
        for rc in rcs:
            fb = GeospatialService.COORDINATES_FALLBACK.get(rc, {})
            nodes.append(GraphNode(
                node_id=rc,
                name=fb.get("city", f"Repair Center {rc}") + " RC",
                node_type="Repair Center",
                latitude=fb.get("lat", 31.0),
                longitude=fb.get("lon", -99.0),
                region=fb.get("state", "TX"),
                city=fb.get("city", "Unknown"),
                capacity=fb.get("capacity", 2000.0)
            ))

        # --- 2. Edges Generation ---
        edges: List[GraphEdge] = []
        if len(tx_df) == 0:
            return nodes, edges

        # Compute transit times if not present
        df_work = tx_df.copy()
        if "Transit_Days" not in df_work.columns:
            order = pd.to_datetime(df_work["Order_Date"], errors="coerce")
            delivery = pd.to_datetime(df_work["Delivery_Date"], errors="coerce")
            df_work["Transit_Days"] = (delivery - order).dt.total_seconds() / 86400.0
            df_work["Transit_Days"] = df_work["Transit_Days"].fillna(0.0).clip(lower=0.0)

        # Aggregate routes (Source + Destination)
        df_work["Route_Key"] = df_work["Origin_Hub"] + " → " + df_work["Destination_Hub"]
        
        for route_key, group in df_work.groupby("Route_Key"):
            first_row = group.iloc[0]
            src = str(first_row["Origin_Hub"])
            dest = str(first_row["Destination_Hub"])

            # Compute route statistics
            avg_dist = float(group["Route_Distance"].mean()) if "Route_Distance" in group.columns else 100.0
            avg_time = float(group["Transit_Days"].mean())
            avg_cost = float(group["Shipment_Cost"].mean()) if "Shipment_Cost" in group.columns else 50.0
            total_qty = float(group["Quantity"].sum())

            # Operational status based on average transit delays
            status = "Active"
            if avg_time > 4.0:
                status = "Disrupted"
            elif avg_time > 2.5:
                status = "Congested"

            dest_capacity = GeospatialService.COORDINATES_FALLBACK.get(dest, {}).get("capacity", 2000.0)

            edges.append(GraphEdge(
                source=src,
                destination=dest,
                distance=round(avg_dist, 2),
                transit_time=round(avg_time, 2),
                cost=round(avg_cost, 2),
                volume=round(total_qty, 2),
                capacity=dest_capacity,
                status=status,
                logistics_partner=str(first_row.get("Logistics_Partner", "Swift LogiCo"))
            ))

        logger.info(f"GraphBuilder: Generated {len(nodes)} nodes and {len(edges)} edges.")
        return nodes, edges

    @classmethod
    def construct_adjacency_structures(
        cls,
        nodes: List[GraphNode],
        edges: List[GraphEdge]
    ) -> Tuple[Dict[str, List[str]], Dict[str, Dict[str, float]], Dict[str, List[Dict[str, Any]]], List[WeightedRouteEntry]]:
        """Generates standard graph structures for network algorithms."""
        logger.info("GraphBuilder: Constructing adjacency list, matrix, neighbor mappings, and routes weights.")

        adj_list: Dict[str, List[str]] = {n.node_id: [] for n in nodes}
        adj_matrix: Dict[str, Dict[str, float]] = {n.node_id: {n2.node_id: float("inf") for n2 in nodes} for n in nodes}
        
        # Self-loops in matrix are 0 weight
        for n in nodes:
            adj_matrix[n.node_id][n.node_id] = 0.0

        neighbor_map: Dict[str, List[Dict[str, Any]]] = {n.node_id: [] for n in nodes}
        weighted_routes: List[WeightedRouteEntry] = []

        for edge in edges:
            src, dest = edge.source, edge.destination

            # Populate adjacency list
            if src in adj_list and dest not in adj_list[src]:
                adj_list[src].append(dest)

            # Populate adjacency matrix (using distance as default shortest weight link)
            if src in adj_matrix and dest in adj_matrix[src]:
                adj_matrix[src][dest] = edge.distance

            # Populate neighbor map details
            if src in neighbor_map:
                neighbor_map[src].append({
                    "destination": dest,
                    "distance": edge.distance,
                    "transit_time": edge.transit_time,
                    "cost": edge.cost,
                    "volume": edge.volume,
                    "status": edge.status,
                    "partner": edge.logistics_partner
                })

            # Weighted routes list
            weighted_routes.append(WeightedRouteEntry(
                source=src,
                destination=dest,
                weight_distance=edge.distance,
                weight_cost=edge.cost,
                weight_time=edge.transit_time
            ))

        return adj_list, adj_matrix, neighbor_map, weighted_routes
