"""Generates index-based 2D matrices for optimization algorithms."""

from typing import List, Dict, Tuple, Any
from backend.models.optimization_metrics import OptimizationNode, OptimizationEdge
from backend.utils.logger import logger


class MatrixGenerator:
    """Constructs dense 2D distance, cost, transit, capacity, and SLA matrices for search engines.

    Stateless generator designed for dependency injection.
    """

    @classmethod
    def generate_matrices(
        cls,
        nodes: List[OptimizationNode],
        edges: List[OptimizationEdge]
    ) -> Tuple[List[List[float]], List[List[float]], List[List[float]], List[List[float]], List[List[float]]]:
        """Generates dense matrices indexed by node matrix_index.

        Args:
            nodes: Preprocessed optimization nodes.
            edges: Preprocessed optimization edges.

        Returns:
            Tuple: distance, cost, transit, capacity, and SLA 2D matrices.
        """
        logger.info("MatrixGenerator: Generating optimization routing matrices.")
        n = len(nodes)

        # Initialize N x N matrices with defaults (inf or 0)
        dist_matrix = [[999999.0 for _ in range(n)] for _ in range(n)]
        cost_matrix = [[999999.0 for _ in range(n)] for _ in range(n)]
        transit_matrix = [[999999.0 for _ in range(n)] for _ in range(n)]
        capacity_matrix = [[0.0 for _ in range(n)] for _ in range(n)]
        sla_matrix = [[0.0 for _ in range(n)] for _ in range(n)]

        # Set self-loops
        for i in range(n):
            dist_matrix[i][i] = 0.0
            cost_matrix[i][i] = 0.0
            transit_matrix[i][i] = 0.0

        # Populate edge metrics
        for edge in edges:
            u, v = edge.source_index, edge.destination_index
            if 0 <= u < n and 0 <= v < n:
                dist_matrix[u][v] = edge.distance
                cost_matrix[u][v] = edge.cost
                transit_matrix[u][v] = edge.transit_time
                capacity_matrix[u][v] = edge.capacity
                # Since SLA is associated with partner/route, we set it here
                sla_matrix[u][v] = 95.0  # nominal target target

        return dist_matrix, cost_matrix, transit_matrix, capacity_matrix, sla_matrix
