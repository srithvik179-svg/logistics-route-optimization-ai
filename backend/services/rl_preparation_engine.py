"""Reinforcement Learning Preparation Engine — Central orchestrator with in-memory caching.

Prepares logistics networks as MDP environments, defining states, actions, rewards,
and simulating sample transition episodes. Benchmarks against Dijkstra, A*, GA, and ACO.
"""

import json
import uuid
from typing import Dict, Any, List

from backend.services.graph_engine import GraphEngine
from backend.services.ant_colony_engine import AntColonyEngine
from backend.services.state_generator import StateGenerator
from backend.services.action_generator import ActionGenerator
from backend.services.episode_manager import EpisodeManager
from backend.models.reward_model import RewardConfig
from backend.models.rl_environment import RLEnvironment, RLEpisode
from backend.utils.logger import logger


class RLPreparationEngine:
    """Orchestrates MDP logistics environment configurations and simulations."""

    _cache: Dict[str, RLEnvironment] = {}

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the in-memory cache."""
        cls._cache.clear()
        logger.info("RL Cache Updated: cache cleared.")

    @classmethod
    def generate_environment(
        cls,
        source: str,
        destination: str,
        filters: Dict[str, Any]
    ) -> RLEnvironment:
        """Constructs a reusable RL MDP environment definition with sample simulation episodes.

        Args:
            source: Starting origin Node ID.
            destination: Final target Node ID.
            filters: Global filters dictionary.

        Returns:
            RLEnvironment: Configured RL environment definition.
        """
        logger.info("RL Preparation Started.")

        # --- Cache Lookup ---
        cache_key = cls._build_cache_key(source, destination, filters)
        if cache_key in cls._cache:
            logger.info("RL Cache Updated: cache hit returned.")
            cached = cls._cache[cache_key]
            cached.cached = True
            return cached

        # Load Graph layout
        graph = GraphEngine.get_graph_payload(filters)
        nodes = [n.node_id for n in graph.nodes]
        neighbor_map = graph.neighbor_mapping

        if source not in neighbor_map or destination not in neighbor_map:
            logger.warning(f"RL Prep warning: Source '{source}' or Destination '{destination}' not in graph. Skipping.")
            empty = cls._empty_environment(source, destination, filters)
            cls._cache[cache_key] = empty
            return empty

        # 1. State Space definitions
        states = StateGenerator.generate_states(nodes, destination, neighbor_map)
        logger.info("States Generated.")

        # 2. Action Space definitions
        actions_list = []
        for node in nodes:
            actions_list.extend(
                ActionGenerator.generate_actions_for_node(node, destination, neighbor_map)
            )
        logger.info("Actions Generated.")

        # 3. Configure rewards and penalty thresholds
        reward_config = RewardConfig()
        logger.info("Reward System Generated.")

        # 4. Generate Benchmark datasets (Dijkstra, A*, GA, ACO)
        # We reuse AntColonyEngine to run all 4 algorithms on this source/destination pair
        aco_payload = AntColonyEngine.optimize_route(source, destination, filters, swarm_size=10, iterations=5)
        benchmarks = aco_payload.benchmarks

        # 5. Simulate demonstration episodes using benchmark paths
        sample_episodes: List[RLEpisode] = []
        
        # Dijkstra path episode
        d_bench = next((b for b in benchmarks if b.algorithm == "Dijkstra"), None)
        if d_bench:
            # Reconstruct Dijkstra path from service
            from backend.services.dijkstra_service import DijkstraService
            dist_weight = lambda edge: float(edge.get("distance", 999.0))
            d_res = DijkstraService.find_shortest_path(nodes, neighbor_map, source, destination, dist_weight)
            if d_res and d_res.path_nodes:
                ep = EpisodeManager.simulate_episode_from_path(
                    f"demo-dijkstra-{uuid.uuid4().hex[:6]}", d_res.path_nodes, destination, neighbor_map, reward_config
                )
                sample_episodes.append(ep)

        # ACO path episode
        if aco_payload.optimized_route and len(aco_payload.optimized_route.path_nodes) >= 2:
            ep = EpisodeManager.simulate_episode_from_path(
                f"demo-aco-{uuid.uuid4().hex[:6]}", aco_payload.optimized_route.path_nodes, destination, neighbor_map, reward_config
            )
            sample_episodes.append(ep)

        logger.info("Episode Definitions Created.")

        # 6. Environmental statistics
        statistics = {
            "total_nodes": len(nodes),
            "state_count": len(states),
            "action_count": len(actions_list),
            "links_ratio": round(len(actions_list) / len(nodes), 2) if nodes else 0.0,
            "demonstrations_loaded": len(sample_episodes)
        }

        env = RLEnvironment(
            environment_id=f"env-{source}-to-{destination}",
            state_space_size=len(states),
            action_space_size=len(actions_list),
            reward_config=reward_config,
            sample_episodes=sample_episodes,
            benchmarks=benchmarks,
            environment_statistics=statistics,
            filters_applied=filters,
            cached=False
        )

        cls._cache[cache_key] = env
        logger.info("RL Cache Updated: cache updated.")
        return env

    # ────────────────────────────────────────────
    # Private Helpers
    # ────────────────────────────────────────────

    @classmethod
    def _build_cache_key(cls, source: str, destination: str, filters: Dict[str, Any]) -> str:
        sorted_items = sorted(
            ((k, v) for k, v in filters.items() if v),
            key=lambda x: x[0]
        )
        return json.dumps((source, destination, sorted_items), default=str)

    @classmethod
    def _empty_environment(cls, source: str, destination: str, filters: Dict[str, Any]) -> RLEnvironment:
        return RLEnvironment(
            environment_id=f"env-empty-{source}-to-{destination}",
            state_space_size=0,
            action_space_size=0,
            reward_config=RewardConfig(),
            sample_episodes=[],
            benchmarks=[],
            environment_statistics={"demonstrations_loaded": 0},
            filters_applied=filters,
            cached=False
        )
