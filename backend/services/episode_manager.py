"""Episode manager service simulating transitions sequences for Reinforcement Learning preparation."""

import uuid
from typing import List, Dict, Any
from backend.models.rl_state import RLState
from backend.models.rl_action import RLAction
from backend.models.reward_model import RewardConfig
from backend.models.rl_environment import RLEpisode, RLEpisodeStep
from backend.services.reward_calculator import RewardCalculator


class EpisodeManager:
    """Simulates agent episodes to verify rewards systems and support bootstrap training."""

    @classmethod
    def simulate_episode_from_path(
        cls,
        episode_id: str,
        path_nodes: List[str],
        destination: str,
        neighbor_map: Dict[str, List[Dict[str, Any]]],
        config: RewardConfig,
        sla_limit_days: float = 3.0
    ) -> RLEpisode:
        """Simulates an RL episode sequence following a specific routing path.

        Args:
            episode_id: Unique ID string.
            path_nodes: Route nodes sequence.
            destination: Final target Node ID.
            neighbor_map: Graph adjacency details.
            config: RewardConfig weights.
            sla_limit_days: Max delivery days before SLA breach.

        Returns:
            RLEpisode: Simulated episode sequence.
        """
        steps: List[RLEpisodeStep] = []
        total_reward = 0.0
        is_success = True

        acc_cost = 0.0
        acc_time = 0.0

        for i in range(len(path_nodes) - 1):
            u = path_nodes[i]
            v = path_nodes[i+1]

            # Get edge details
            neighbors = neighbor_map.get(u, [])
            edge = next((e for e in neighbors if e["destination"] == v), {})

            cost = float(edge.get("cost", 50.0))
            transit = float(edge.get("transit_time", 1.0))
            cap = float(edge.get("capacity", 200.0))

            # Prior State
            prior_state = RLState(
                current_hub=u,
                destination_hub=destination,
                accumulated_cost=acc_cost,
                accumulated_time=acc_time,
                remaining_capacity=cap,
                sla_status="within_sla" if acc_time <= sla_limit_days else "breached"
            )

            # Update accumulated metrics
            acc_cost += cost
            acc_time += transit

            # Next State
            next_state = RLState(
                current_hub=v,
                destination_hub=destination,
                accumulated_cost=acc_cost,
                accumulated_time=acc_time,
                remaining_capacity=cap - 10.0,
                sla_status="within_sla" if acc_time <= sla_limit_days else "breached"
            )

            # Action selected
            action = RLAction(
                action_type="MOVE_TO_ADJACENT",
                target_hub=v,
                partner_id=edge.get("partner"),
                capacity_allocation=10.0
            )

            # Calculate step reward
            reward = RewardCalculator.calculate_transition_reward(
                prior_state, action, next_state, neighbor_map, config
            )
            total_reward += reward

            steps.append(
                RLEpisodeStep(
                    step_index=i,
                    state=prior_state,
                    action=action,
                    next_state=next_state,
                    reward=reward,
                    is_terminal=False
                )
            )

            if next_state.sla_status == "breached":
                is_success = False

        # Add TERMINATE_ROUTE step if we reached the end
        if path_nodes:
            final_node = path_nodes[-1]
            final_state = RLState(
                current_hub=final_node,
                destination_hub=destination,
                accumulated_cost=acc_cost,
                accumulated_time=acc_time,
                remaining_capacity=150.0,
                sla_status="within_sla" if acc_time <= sla_limit_days else "breached"
            )

            terminate_action = RLAction(
                action_type="TERMINATE_ROUTE",
                target_hub=None,
                partner_id=None,
                capacity_allocation=None
            )

            reward = RewardCalculator.calculate_transition_reward(
                final_state, terminate_action, final_state, neighbor_map, config
            )
            total_reward += reward

            steps.append(
                RLEpisodeStep(
                    step_index=len(steps),
                    state=final_state,
                    action=terminate_action,
                    next_state=final_state,
                    reward=reward,
                    is_terminal=True
                )
            )

            if final_node != destination:
                is_success = False

        return RLEpisode(
            episode_id=episode_id,
            steps=steps,
            total_reward=round(total_reward, 4),
            is_success=is_success
        )
