"""Transition probability service implementing roulette wheel choice selection for swarm paths construction."""

import random
from typing import List, Dict, Any, Set, Optional


class TransitionProbabilityService:
    """Calculates probabilities and selects the next node hop for artificial ants."""

    @classmethod
    def select_next_node(
        cls,
        current_node: str,
        visited_nodes: Set[str],
        neighbor_map: Dict[str, List[Dict[str, Any]]],
        pheromone_matrix: Dict[str, Dict[str, float]],
        alpha: float = 1.0,
        beta: float = 2.0
    ) -> Optional[str]:
        """Selects the next node in the path construction using roulette wheel choice.

        Args:
            current_node: Current Node ID of the ant.
            visited_nodes: Set of Node IDs already visited by the ant.
            neighbor_map: Adjacency list detailed edges.
            pheromone_matrix: Active pheromone levels matrix.
            alpha: Pheromone sensitivity weight exponent.
            beta: Heuristic visibility sensitivity weight exponent.

        Returns:
            Optional[str]: Selected Node ID, or None if stuck.
        """
        neighbors = neighbor_map.get(current_node, [])
        unvisited = [n for n in neighbors if n["destination"] not in visited_nodes]

        if not unvisited:
            return None

        weights = []
        for edge in unvisited:
            v = edge["destination"]
            
            # Pheromone level lookup
            tau = 0.01
            if current_node in pheromone_matrix and v in pheromone_matrix[current_node]:
                tau = pheromone_matrix[current_node][v]

            # Heuristic visibility: inverse of distance
            dist = float(edge.get("distance", 999.0))
            if dist <= 0:
                dist = 1.0
            eta = 100.0 / dist

            # Numerator weight f = tau^alpha * eta^beta
            weight = (tau ** alpha) * (eta ** beta)
            weights.append((v, weight))

        total_weight = sum(w[1] for w in weights)

        if total_weight == 0:
            # Random selection if all weights are zero
            return random.choice([edge["destination"] for edge in unvisited])

        # Roulette wheel selection
        r = random.uniform(0.0, total_weight)
        cumulative = 0.0
        for node_id, weight in weights:
            cumulative += weight
            if r <= cumulative:
                return node_id

        return weights[-1][0]
