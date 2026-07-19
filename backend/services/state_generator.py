"""State space generator service for Reinforcement Learning preparation."""

from typing import List, Dict, Any
from backend.models.rl_state import RLState


class StateGenerator:
    """Generates RLState representation spaces based on network topology."""

    @classmethod
    def generate_states(
        cls,
        nodes: List[str],
        destination: str,
        neighbor_map: Dict[str, List[Dict[str, Any]]],
        capacity_map: Dict[str, float] = None
    ) -> List[RLState]:
        """Generates possible states for all active graph nodes targeting the destination.

        Args:
            nodes: List of all active Node IDs.
            destination: Final target Node ID.
            neighbor_map: Adjacency mappings detailing links.
            capacity_map: Map of node or link capacity levels.

        Returns:
            List[RLState]: List of generated RLState objects.
        """
        states = []
        
        for node in nodes:
            # Determine remaining capacity (defaulting to 150.0 units or mock lookup)
            rem_cap = 150.0
            if capacity_map and node in capacity_map:
                rem_cap = capacity_map[node]

            # Approximate congestion or partner counts
            neighbors = neighbor_map.get(node, [])
            congestion = 0.15 if len(neighbors) > 3 else 0.05
            partner_avail = 1.0 if len(neighbors) > 0 else 0.0

            states.append(
                RLState(
                    current_hub=node,
                    destination_hub=destination,
                    accumulated_cost=0.0,
                    accumulated_time=0.0,
                    remaining_capacity=rem_cap,
                    sla_status="within_sla",
                    partner_availability=partner_avail,
                    network_congestion=congestion,
                    route_score=75.0 if node != destination else 100.0
                )
            )

        return states
