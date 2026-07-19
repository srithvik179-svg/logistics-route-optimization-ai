"""Initializer service generating the swarm artificial ants population."""

from typing import List
from backend.models.ant import Ant


class AntInitializer:
    """Generates the initial swarm set of ants at the source node."""

    @classmethod
    def initialize_ants(cls, source: str, swarm_size: int) -> List[Ant]:
        """Creates swarm_size ants starting at the source node ID.

        Args:
            source: Origin Node ID.
            swarm_size: Total number of ants to initialize.

        Returns:
            List[Ant]: Initialized ants list.
        """
        return [
            Ant(
                path_nodes=[source],
                distance=0.0,
                cost=0.0,
                transit_time=0.0,
                is_feasible=False,
                fitness=0.0
            ) for _ in range(swarm_size)
        ]
