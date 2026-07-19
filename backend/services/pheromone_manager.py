"""Pheromone manager service for swarming intelligence route search loops."""

from typing import Dict, List, Any
from backend.models.pheromone_matrix import PheromoneMatrix
from backend.utils.logger import logger


class PheromoneManager:
    """Manages evaporation and deposition of pheromone levels across graph edges."""

    def __init__(self, nodes: List[str], neighbor_map: Dict[str, List[Dict[str, Any]]], initial_level: float = 1.0) -> None:
        """Initializes the pheromone matrix mapping.

        Args:
            nodes: List of all Node IDs in the graph.
            neighbor_map: Adjacency map detailing node edges.
            initial_level: Base initial level of pheromone on each active edge.
        """
        self.matrix: Dict[str, Dict[str, float]] = {}
        
        # Initialize pheromones only on active graph edges
        for u in nodes:
            self.matrix[u] = {}
            for edge in neighbor_map.get(u, []):
                v = edge["destination"]
                self.matrix[u][v] = initial_level

        logger.info("Pheromone Matrix Generated.")

    def evaporate(self, rho: float, min_pheromone: float = 0.01) -> None:
        """Evaporates pheromone levels across all edges: tau = (1 - rho) * tau.

        Args:
            rho: Evaporation rate fraction.
            min_pheromone: Floor value to prevent pheromone dropping to absolute zero.
        """
        for u in self.matrix:
            for v in self.matrix[u]:
                evap_val = self.matrix[u][v] * (1.0 - rho)
                self.matrix[u][v] = max(min_pheromone, evap_val)

    def deposit_pheromone(self, path: List[str], amount: float) -> None:
        """Deposits pheromones on the edges traversed in a route.

        Args:
            path: Route Node IDs sequence.
            amount: Pheromone deposit amount value.
        """
        if len(path) < 2:
            return

        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            if u in self.matrix and v in self.matrix[u]:
                self.matrix[u][v] += amount

    def get_pheromone_matrix_model(self) -> PheromoneMatrix:
        """Returns the PheromoneMatrix schema model representation."""
        return PheromoneMatrix(matrix=self.matrix)
