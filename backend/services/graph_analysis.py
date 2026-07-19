"""Connectivity analysis service identifying dead-ends, highly connected hubs, critical connections, and bridge routes."""

from typing import List, Dict, Set
import numpy as np

from backend.models.graph_metrics import ConnectivityAnalysis, GraphNode, GraphEdge
from backend.utils.logger import logger


class GraphAnalysisService:
    """Performs advanced connectivity analysis on network graphs to find vulnerabilities.

    Stateless service designed for dependency injection.
    """

    @classmethod
    def analyze_connectivity(
        cls,
        nodes: List[GraphNode],
        edges: List[GraphEdge],
        components_count: int
    ) -> ConnectivityAnalysis:
        """Evaluates topological routes to detect dead-ends, bridges, and critical connection points.

        Args:
            nodes: Nodes list.
            edges: Edges list.
            components_count: Base count of undirected connected components.

        Returns:
            ConnectivityAnalysis payload container.
        """
        logger.info("GraphAnalysisService: Analyzing graph connectivity.")

        analysis = ConnectivityAnalysis()
        if not nodes:
            return analysis

        # 1. Degrees mapping (directed in/out degree counts)
        in_degrees: Dict[str, int] = {n.node_id: 0 for n in nodes}
        out_degrees: Dict[str, int] = {n.node_id: 0 for n in nodes}

        for edge in edges:
            src, dest = edge.source, edge.destination
            if src in out_degrees:
                out_degrees[src] += 1
            if dest in in_degrees:
                in_degrees[dest] += 1

        # 2. Dead-end nodes (in-degree == 0 OR out-degree == 0)
        for n in nodes:
            n_id = n.node_id
            if in_degrees.get(n_id, 0) == 0 or out_degrees.get(n_id, 0) == 0:
                analysis.dead_end_nodes.append(n_id)

        # 3. Highly connected hubs (degree > avg_degree + 1.5 * std_dev)
        degrees = [in_degrees.get(n.node_id, 0) + out_degrees.get(n.node_id, 0) for n in nodes]
        if len(degrees) > 0:
            avg_deg = np.mean(degrees)
            std_deg = np.std(degrees)
            threshold = avg_deg + 1.5 * std_deg if std_deg > 0 else avg_deg + 1.0

            for n in nodes:
                n_id = n.node_id
                deg = in_degrees.get(n_id, 0) + out_degrees.get(n_id, 0)
                if deg >= threshold:
                    analysis.highly_connected_hubs.append(n_id)

        # 4. Critical connections (edges with highest volume load, e.g. top 3 routes by shipment quantity)
        sorted_edges = sorted(edges, key=lambda x: x.volume, reverse=True)
        for edge in sorted_edges[:3]:
            analysis.critical_connections.append(f"{edge.source} → {edge.destination}")

        # 5. Bridge routes (cut-edges)
        # An edge is a bridge if removing it increases the connected components count.
        for edge in edges:
            src, dest = edge.source, edge.destination
            
            # Construct undirected adjacency list excluding this edge
            undirected_adj: Dict[str, Set[str]] = {n.node_id: set() for n in nodes}
            for e2 in edges:
                if e2 == edge:
                    continue
                s2, d2 = e2.source, e2.destination
                if s2 in undirected_adj and d2 in undirected_adj:
                    undirected_adj[s2].add(d2)
                    undirected_adj[d2].add(s2)

            # Recalculate components
            visited: Set[str] = set()
            test_components = 0
            for n in nodes:
                n_id = n.node_id
                if n_id not in visited:
                    test_components += 1
                    queue = [n_id]
                    visited.add(n_id)
                    while queue:
                        curr = queue.pop(0)
                        for neighbor in undirected_adj.get(curr, []):
                            if neighbor not in visited:
                                visited.add(neighbor)
                                queue.append(neighbor)

            if test_components > components_count:
                analysis.bridge_routes.append(f"{src} → {dest}")

        return analysis
