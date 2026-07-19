"""Reward calculator service evaluating state transitions and penalties for Reinforcement Learning preparation."""

from typing import Dict, Any, List
from backend.models.rl_state import RLState
from backend.models.rl_action import RLAction
from backend.models.reward_model import RewardConfig


class RewardCalculator:
    """Computes rewards and penalties for MDP agent transitions."""

    @classmethod
    def calculate_transition_reward(
        cls,
        state: RLState,
        action: RLAction,
        next_state: RLState,
        neighbor_map: Dict[str, List[Dict[str, Any]]],
        config: RewardConfig
    ) -> float:
        """Calculates step reward R(S, A, S').

        Args:
            state: Initial RLState.
            action: Selected RLAction.
            next_state: Resulting RLState.
            neighbor_map: Adjacency list.
            config: RewardConfig coefficients.

        Returns:
            float: Numerical reward or penalty value.
        """
        # 1. Termination checks
        if action.action_type == "TERMINATE_ROUTE":
            if state.current_hub == state.destination_hub:
                # Successfully arrived!
                return 150.0 + config.reward_efficiency_weight * state.route_score
            else:
                # Quit early or stuck!
                return config.penalty_invalid_route

        u = state.current_hub
        v = next_state.current_hub

        # 2. Invalid node transitions
        neighbors = neighbor_map.get(u, [])
        edge = next(
            (e for e in neighbors if e["destination"] == v),
            None
        )

        if not edge:
            return config.penalty_invalid_route

        # 3. Base cost/time penalties (lower is better, so negative reinforcement)
        cost = float(edge.get("cost", 100.0))
        transit_time = float(edge.get("transit_time", 2.0))

        step_reward = -(
            cost * config.reward_cost_weight +
            transit_time * config.reward_time_weight
        )

        # 4. Capacity overflow penalty
        if next_state.remaining_capacity < 0:
            step_reward += config.penalty_capacity_overflow

        # 5. SLA violation penalty
        if next_state.sla_status == "breached":
            step_reward += config.penalty_sla_breach

        # 6. Small progress reward if getting closer to destination
        step_reward += 5.0  # constant step progress nudge

        return round(step_reward, 4)
