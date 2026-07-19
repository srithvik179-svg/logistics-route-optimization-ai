"""Logistics network graph preprocessor for optimization systems."""

from typing import List, Dict, Tuple, Any
from backend.models.graph_metrics import GraphNode, GraphEdge
from backend.models.optimization_metrics import OptimizationNode, OptimizationEdge, NetworkBaselines
from backend.utils.logger import logger


class GraphPreprocessor:
    """Preprocesses graph structures, indexes nodes, normalizes weights, and calculates operational baselines.

    Stateless preprocessing service designed for dependency injection.
    """

    @classmethod
    def preprocess_nodes(
        cls,
        nodes: List[GraphNode]
    ) -> Tuple[List[OptimizationNode], Dict[str, int]]:
        """Maps node IDs to matrix integer indices and normalizes node capacities.

        Args:
            nodes: Nodes list.

        Returns:
            Tuple[List[OptimizationNode], Dict[str, int]]: Preprocessed nodes and ID-to-index mapping.
        """
        logger.info("GraphPreprocessor: Mapping nodes to matrix indices.")
        
        opt_nodes = []
        node_indices = {}

        max_capacity = max(n.capacity for n in nodes) if nodes else 1.0
        if max_capacity == 0:
            max_capacity = 1.0

        for idx, node in enumerate(nodes):
            node_indices[node.node_id] = idx
            
            # Normalize capacity between 0.0 and 1.0
            norm_score = node.capacity / max_capacity

            opt_nodes.append(OptimizationNode(
                node_id=node.node_id,
                matrix_index=idx,
                node_type=node.node_type,
                capacity=node.capacity,
                normalized_score=round(norm_score, 4)
            ))

        return opt_nodes, node_indices

    @classmethod
    def preprocess_edges(
        cls,
        edges: List[GraphEdge],
        node_indices: Dict[str, int]
    ) -> List[OptimizationEdge]:
        """Calculates normalized cost/distance weights for routing loops.

        Args:
            edges: Edges list.
            node_indices: Node ID to matrix index mapping dictionary.

        Returns:
            List[OptimizationEdge]: Optimization-ready edges list.
        """
        logger.info("GraphPreprocessor: Normalizing edge weights.")
        opt_edges = []

        max_cost = max(e.cost for e in edges) if edges else 1.0
        if max_cost == 0:
            max_cost = 1.0

        for edge in edges:
            src, dest = edge.source, edge.destination
            src_idx = node_indices.get(src, -1)
            dest_idx = node_indices.get(dest, -1)

            # Normalized weight: 80% cost + 20% distance (rescaled to 0-1)
            norm_cost = edge.cost / max_cost
            norm_dist = edge.distance / 600.0  # reference 600mi max distance
            norm_weight = 0.80 * norm_cost + 0.20 * min(1.0, norm_dist)

            opt_edges.append(OptimizationEdge(
                source=src,
                destination=dest,
                source_index=src_idx,
                destination_index=dest_idx,
                distance=edge.distance,
                cost=edge.cost,
                transit_time=edge.transit_time,
                capacity=edge.capacity,
                volume=edge.volume,
                status=edge.status,
                normalized_weight=round(norm_weight, 4)
            ))

        return opt_edges

    @classmethod
    def calculate_baselines(
        cls,
        edges: List[GraphEdge],
        route_scores: List[Any]
    ) -> NetworkBaselines:
        """Aggregates route scoring and operational details to compute baselines.

        Args:
            edges: Graph edges list.
            route_scores: Route score results.

        Returns:
            NetworkBaselines: Aggregated baselines.
        """
        if not edges:
            return NetworkBaselines(
                baseline_cost=0.0, baseline_transit_time=0.0, baseline_capacity_utilization=0.0,
                baseline_sla_compliance=0.0, baseline_operational_efficiency=0.0,
                baseline_route_performance=0.0
            )

        avg_cost = sum(e.cost for e in edges) / len(edges)
        avg_time = sum(e.transit_time for e in edges) / len(edges)
        
        # Utilization baseline fraction
        utils = [(e.volume / e.capacity) if e.capacity > 0 else 0.5 for e in edges]
        avg_util = sum(utils) / len(utils)

        # Map compliance and scoring averages from route scoring results
        sla_scores = [r.sla_score for r in route_scores] if route_scores else [95.0]
        avg_sla = sum(sla_scores) / len(sla_scores)

        overall_scores = [r.overall_route_score for r in route_scores] if route_scores else [80.0]
        avg_overall = sum(overall_scores) / len(overall_scores)

        perf_indices = [r.performance_index for r in route_scores] if route_scores else [80.0]
        avg_perf = sum(perf_indices) / len(perf_indices)

        return NetworkBaselines(
            baseline_cost=round(avg_cost, 2),
            baseline_transit_time=round(avg_time, 2),
            baseline_capacity_utilization=round(avg_util, 4),
            baseline_sla_compliance=round(avg_sla, 2),
            baseline_operational_efficiency=round(avg_overall, 2),
            baseline_route_performance=round(avg_perf, 2)
        )
