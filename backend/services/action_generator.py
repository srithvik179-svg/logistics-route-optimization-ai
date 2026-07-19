"""Action space generator service for Reinforcement Learning preparation."""

from typing import List, Dict, Any
from backend.models.rl_action import RLAction


class ActionGenerator:
    """Generates available action options for any given state hub."""

    @classmethod
    def generate_actions_for_node(
        cls,
        node: str,
        destination: str,
        neighbor_map: Dict[str, List[Dict[str, Any]]]
    ) -> List[RLAction]:
        """Calculates legal decision actions from a current state hub.

        Args:
            node: Current Node ID.
            destination: Final target Node ID.
            neighbor_map: Adjacency list detailed links.

        Returns:
            List[RLAction]: Active actions list.
        """
        actions = []

        # If we have reached the destination, we can only terminate the route
        if node == destination:
            actions.append(
                RLAction(
                    action_type="TERMINATE_ROUTE",
                    target_hub=None,
                    partner_id=None,
                    capacity_allocation=None
                )
            )
            return actions

        neighbors = neighbor_map.get(node, [])

        for edge in neighbors:
            v = edge["destination"]
            partner = edge.get("partner", "DEFAULT_PARTNER")
            dist = float(edge.get("distance", 100.0))

            # 1. Move action
            actions.append(
                RLAction(
                    action_type="MOVE_TO_ADJACENT",
                    target_hub=v,
                    partner_id=None,
                    capacity_allocation=None
                )
            )

            # 2. Partner action
            actions.append(
                RLAction(
                    action_type="CHOOSE_PARTNER",
                    target_hub=v,
                    partner_id=partner,
                    capacity_allocation=None
                )
            )

            # 3. Capacity allocation action
            actions.append(
                RLAction(
                    action_type="ALLOCATE_CAPACITY",
                    target_hub=v,
                    partner_id=None,
                    capacity_allocation=50.0  # standard volume allocation unit
                )
            )

        # Alternates or fallback actions
        if not neighbors:
            actions.append(
                RLAction(
                    action_type="TERMINATE_ROUTE",
                    target_hub=None,
                    partner_id=None,
                    capacity_allocation=None
                )
            )

        return actions
