"""Constraint validation service verifying graph consistency and network integrity for path search loops."""

from typing import List, Dict
from backend.models.graph_metrics import GraphNode, GraphEdge
from backend.models.optimization_metrics import GraphValidationResult, OptimizationConstraints
from backend.utils.logger import logger


class ConstraintValidator:
    """Validates structural integrity, duplicate routes, negative weights, and disconnected nodes.

    Stateless validator designed for dependency injection.
    """

    @classmethod
    def validate_graph(
        cls,
        nodes: List[GraphNode],
        edges: List[GraphEdge],
        components_count: int
    ) -> GraphValidationResult:
        """Runs integrity checks on network topological elements to verify readiness.

        Args:
            nodes: Nodes list.
            edges: Edges list.
            components_count: Number of disconnected subnetworks.

        Returns:
            GraphValidationResult payload.
        """
        logger.info("ConstraintValidator: Validating network graph constraints.")
        warnings = []

        # 1. Missing Nodes validation
        node_ids = {n.node_id for n in nodes}
        for edge in edges:
            if edge.source not in node_ids:
                warnings.append(f"Missing node definition for origin ID: {edge.source}")
            if edge.destination not in node_ids:
                warnings.append(f"Missing node definition for destination ID: {edge.destination}")

        # 2. Duplicate Edges detection
        route_keys = []
        has_dup = False
        for edge in edges:
            key = (edge.source, edge.destination)
            if key in route_keys:
                has_dup = True
                warnings.append(f"Duplicate route link registered: {edge.source} → {edge.destination}")
            route_keys.append(key)

        # 3. Negative Edge Weights detection
        has_neg = False
        for edge in edges:
            if edge.distance < 0:
                has_neg = True
                warnings.append(f"Negative distance weight on route {edge.source} → {edge.destination}: {edge.distance}")
            if edge.cost < 0:
                has_neg = True
                warnings.append(f"Negative cost weight on route {edge.source} → {edge.destination}: {edge.cost}")

        # 4. Disconnected Components warning
        if components_count > 1:
            warnings.append(f"Graph is disconnected into {components_count} sub-networks.")

        # Determine overall validity (strict: invalid if missing nodes or negative weights)
        is_valid = True
        if has_neg or any("Missing node" in w for w in warnings):
            is_valid = False

        return GraphValidationResult(
            has_warnings=len(warnings) > 0,
            is_valid=is_valid,
            warnings=warnings,
            disconnected_components_count=components_count,
            has_negative_weights=has_neg,
            has_duplicate_edges=has_dup
        )

    @classmethod
    def get_standard_constraints(cls) -> OptimizationConstraints:
        """Exposes standard maximum threshold limits for route validation queries."""
        return OptimizationConstraints(
            max_distance_limit=450.0,      # limit transit distance to 450 miles
            max_cost_limit=350.0,          # limit shipment transport cost to $350
            max_transit_time_limit=3.5,    # limit delivery duration to 3.5 days
            min_sla_target_compliance=90.0 # SLA compliance must be >= 90%
        )
