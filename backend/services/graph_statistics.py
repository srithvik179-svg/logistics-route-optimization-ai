"""Stateless calculator for topological graph statistics and route breakdowns."""

import pandas as pd
from typing import List, Dict, Any, Tuple, Set
from backend.models.graph_metrics import GraphOverviewStats, GraphNode, GraphEdge
from backend.utils.logger import logger


class GraphStatistics:
    """Computes network topology statistics, degrees, connected components, density, and breakdowns.

    Stateless service designed for dependency injection.
    """

    @classmethod
    def compute_statistics(
        cls,
        nodes: List[GraphNode],
        edges: List[GraphEdge],
        adj_list: Dict[str, List[str]]
    ) -> Tuple[GraphOverviewStats, List[List[str]]]:
        """Calculates topological graph overview stats and discovers connected components.

        Args:
            nodes: List of nodes.
            edges: List of edges.
            adj_list: Adjacency list map.

        Returns:
            Tuple[GraphOverviewStats, List[List[str]]]: calculated stats and list of connected component subsets.
        """
        logger.info("GraphStatistics: Computing topological statistics.")

        total_nodes = len(nodes)
        total_edges = len(edges)

        zeros = (GraphOverviewStats(
            total_nodes=total_nodes, total_edges=0, avg_node_degree=0.0,
            max_degree=0, min_degree=0, connected_components=total_nodes,
            isolated_nodes=total_nodes, graph_density=0.0, avg_route_length=0.0
        ), [[n.node_id] for n in nodes])

        if total_nodes == 0:
            return zeros

        # Calculate degrees (directed: in_degree + out_degree)
        in_degrees: Dict[str, int] = {n.node_id: 0 for n in nodes}
        out_degrees: Dict[str, int] = {n.node_id: 0 for n in nodes}

        for edge in edges:
            src, dest = edge.source, edge.destination
            if src in out_degrees:
                out_degrees[src] += 1
            if dest in in_degrees:
                in_degrees[dest] += 1

        total_degrees: Dict[str, int] = {}
        isolated_count = 0
        for n in nodes:
            n_id = n.node_id
            deg = in_degrees.get(n_id, 0) + out_degrees.get(n_id, 0)
            total_degrees[n_id] = deg
            if deg == 0:
                isolated_count += 1

        degrees_list = list(total_degrees.values())
        avg_deg = sum(degrees_list) / total_nodes
        max_deg = max(degrees_list) if degrees_list else 0
        min_deg = min(degrees_list) if degrees_list else 0

        # Discover connected components using BFS (undirected traversal behavior)
        # Construct undirected adjacency mapping
        undirected_adj: Dict[str, Set[str]] = {n.node_id: set() for n in nodes}
        for edge in edges:
            src, dest = edge.source, edge.destination
            if src in undirected_adj and dest in undirected_adj:
                undirected_adj[src].add(dest)
                undirected_adj[dest].add(src)

        visited: Set[str] = set()
        components: List[List[str]] = []

        for n in nodes:
            n_id = n.node_id
            if n_id not in visited:
                comp = []
                queue = [n_id]
                visited.add(n_id)

                while queue:
                    curr = queue.pop(0)
                    comp.append(curr)

                    for neighbor in undirected_adj.get(curr, []):
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                components.append(comp)

        # Graph density for directed graph: E / (V * (V - 1))
        density = 0.0
        if total_nodes > 1:
            density = total_edges / (total_nodes * (total_nodes - 1))

        # Average route length (distance edge weights average)
        avg_len = sum(e.distance for e in edges) / total_edges if total_edges > 0 else 0.0

        stats = GraphOverviewStats(
            total_nodes=total_nodes,
            total_edges=total_edges,
            avg_node_degree=round(avg_deg, 2),
            max_degree=max_deg,
            min_degree=min_deg,
            connected_components=len(components),
            isolated_nodes=isolated_count,
            graph_density=round(density, 4),
            avg_route_length=round(avg_len, 2)
        )

        logger.info("GraphStatistics: Graph Statistics Generated.")
        return stats, components
