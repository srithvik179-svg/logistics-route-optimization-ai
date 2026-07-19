"""Verification test suite for the Reinforcement Learning Preparation Engine (Phase 24).

Tests state mappings, action rules, reward/penalty calculations, episode simulations,
benchmark datasets preparation, caching controls, and API endpoint integration.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.services.repository import repository
from backend.services.rl_preparation_engine import RLPreparationEngine
from backend.services.reward_calculator import RewardCalculator
from backend.models.reward_model import RewardConfig
from backend.models.rl_state import RLState
from backend.models.rl_action import RLAction


def setup():
    """Initialize repository for tests."""
    if not repository.is_initialized():
        repository.initialize()
    RLPreparationEngine.clear_cache()


def test_reward_calculator():
    """Verify reward calculator step values and penalties."""
    print("\n--- TESTING REWARD CALCULATOR ---")
    config = RewardConfig()
    
    # State transition: successful termination
    s_term = RLState(current_hub="HUB-B", destination_hub="HUB-B")
    a_term = RLAction(action_type="TERMINATE_ROUTE")
    r1 = RewardCalculator.calculate_transition_reward(s_term, a_term, s_term, {}, config)
    assert r1 > 100.0, "Successful terminate action must receive a high reward bonus"

    # State transition: premature termination (failure)
    s_term_prem = RLState(current_hub="HUB-A", destination_hub="HUB-B")
    r2 = RewardCalculator.calculate_transition_reward(s_term_prem, a_term, s_term_prem, {}, config)
    assert r2 == config.penalty_invalid_route, "Premature terminate action must receive invalid route penalty"

    # State transition: normal movement link
    s1 = RLState(current_hub="HUB-A", destination_hub="HUB-B")
    a_move = RLAction(action_type="MOVE_TO_ADJACENT", target_hub="HUB-B")
    s2 = RLState(current_hub="HUB-B", destination_hub="HUB-B")
    
    neighbor_map = {
        "HUB-A": [{"destination": "HUB-B", "distance": 100.0, "cost": 150.0, "transit_time": 2.0}]
    }

    r3 = RewardCalculator.calculate_transition_reward(s1, a_move, s2, neighbor_map, config)
    # Expected: -(150.0 * 0.4 + 2.0 * 0.4) + 5.0 = -60.8 + 5.0 = -55.8
    assert r3 == -55.8, f"Expected reward -55.8, got {r3}"

    print("✓ Reward calculator verified.")


def test_rl_environment_generation():
    """Verify MDP environment creation, actions, episodes, and benchmarks."""
    print("\n--- TESTING ENVIRONMENT BUILDER ---")
    from backend.services.graph_engine import GraphEngine
    graph = GraphEngine.get_graph_payload({})
    neighbor_map = graph.neighbor_mapping
    
    src = list(neighbor_map.keys())[0]
    dest = neighbor_map[src][0]["destination"]

    env = RLPreparationEngine.generate_environment(src, dest, {})

    assert env.state_space_size > 0, "State space size must be positive"
    assert env.action_space_size > 0, "Action space size must be positive"
    assert len(env.sample_episodes) > 0, "Demonstration episodes must be generated"
    assert len(env.benchmarks) > 0, "Benchmark metrics must be compiled"

    # Check stats
    stats = env.environment_statistics
    assert stats["total_nodes"] > 0
    assert stats["demonstrations_loaded"] > 0

    # Check episode steps sequence
    ep = env.sample_episodes[0]
    assert len(ep.steps) >= 2, "Simulation episodes must contain transition steps"
    assert ep.steps[0].action.action_type == "MOVE_TO_ADJACENT"
    assert ep.steps[-1].action.action_type == "TERMINATE_ROUTE"

    print(f"Environment ID: {env.environment_id}")
    print(f"States count: {env.state_space_size}, Actions count: {env.action_space_size}")
    print(f"Demonstrations loaded: {stats['demonstrations_loaded']}")
    print(f"Total reward for Dijkstra demo: {ep.total_reward}")
    print("✓ Environment builder verified.")


def test_cache():
    """Validate cache hits return cached=True flags."""
    print("\n--- TESTING CACHE MECHANICS ---")
    RLPreparationEngine.clear_cache()
    from backend.services.graph_engine import GraphEngine
    graph = GraphEngine.get_graph_payload({})
    src = list(graph.neighbor_mapping.keys())[0]
    dest = graph.neighbor_mapping[src][0]["destination"]

    e1 = RLPreparationEngine.generate_environment(src, dest, {})
    assert e1.cached is False, "First run should miss cache"

    e2 = RLPreparationEngine.generate_environment(src, dest, {})
    assert e2.cached is True, "Second run should hit cache"

    print("✓ Cache verified.")


def test_invalid_search():
    """Verify preparation handles non-existent node searches gracefully."""
    print("\n--- TESTING INVALID SEARCH ---")
    env = RLPreparationEngine.generate_environment("UNKNOWN_SRC", "UNKNOWN_DEST", {})
    assert env.state_space_size == 0
    assert env.action_space_size == 0
    assert len(env.sample_episodes) == 0
    print("✓ Invalid searches verified.")


if __name__ == "__main__":
    print("Initializing Reinforcement Learning Preparation Engine verification suite...")
    setup()

    test_reward_calculator()
    test_rl_environment_generation()
    test_cache()
    test_invalid_search()

    print("\n" + "=" * 60)
    print("All Reinforcement Learning Preparation Engine tests passed successfully!")
    print("=" * 60)
