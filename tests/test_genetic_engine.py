"""Verification test suite for the Genetic Algorithm Optimization Engine (Phase 22).

Tests route chromosome selection crossovers, random walks mutations, business constraints evaluation,
population diversity metrics, convergence early stopping, and caching layers.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.services.repository import repository
from backend.services.genetic_algorithm_engine import GeneticAlgorithmEngine
from backend.services.fitness_calculator import FitnessCalculator
from backend.models.optimization_metrics import OptimizationConstraints


def setup():
    """Initialize repository for tests."""
    if not repository.is_initialized():
        repository.initialize()
    GeneticAlgorithmEngine.clear_cache()


def test_fitness_calculations():
    """Verify route evaluation and constraints violation penalties."""
    print("\n--- TESTING FITNESS CALCULATOR ---")
    cons = OptimizationConstraints(
        max_distance_limit=450.0,
        max_cost_limit=350.0,
        max_transit_time_limit=3.5,
        min_sla_target_compliance=90.0
    )

    # 1. Feasible test path using mock neighbor map (to avoid database congested capacity overloads)
    mock_neighbor_map = {
        "node_1": [
            {
                "destination": "node_2",
                "distance": 100.0,
                "cost": 50.0,
                "transit_time": 1.0,
                "volume": 10.0,
                "capacity": 100.0
            }
        ],
        "node_2": []
    }
    path = ["node_1", "node_2"]

    scored = FitnessCalculator.calculate_fitness(path, mock_neighbor_map, cons)
    assert scored.fitness > 0, "Fitness must be positive"
    assert scored.is_feasible is True, "Mock path should be feasible under generous constraints"

    # 2. Infeasible path (forcing limit exceedance)
    strict_cons = OptimizationConstraints(
        max_distance_limit=5.0,  # too strict, will violate distance limit
        max_cost_limit=5.0,
        max_transit_time_limit=0.1,
        min_sla_target_compliance=99.0
    )
    penalized = FitnessCalculator.calculate_fitness(path, mock_neighbor_map, strict_cons)
    assert penalized.is_feasible is False, "Chromosome must be flagged infeasible"
    assert penalized.fitness < scored.fitness, "Penalized chromosome fitness must be smaller"

    print("✓ Fitness Calculator verified.")


def test_genetic_evolution():
    """Verify full evolutionary optimization and generational stats tracking."""
    print("\n--- TESTING GA EVOLUTION ---")
    from backend.services.graph_engine import GraphEngine
    graph = GraphEngine.get_graph_payload({})
    neighbor_map = graph.neighbor_mapping
    
    src = list(neighbor_map.keys())[0]
    dest = neighbor_map[src][0]["destination"]

    payload = GeneticAlgorithmEngine.optimize_route(
        src, dest, {}, population_size=10, generations=15
    )

    assert payload.optimized_route is not None, "Optimization must return a solution"
    assert len(payload.generation_history) > 0, "Generation stats must be recorded"
    assert len(payload.fitness_history) == len(payload.generation_history)

    # Inspect final chromosome properties
    opt = payload.optimized_route
    assert opt.fitness > 0
    assert len(opt.path_nodes) >= 2
    assert opt.path_nodes[0] == src
    assert opt.path_nodes[-1] == dest

    # Check stats ranges
    first_gen = payload.generation_history[0]
    last_gen = payload.generation_history[-1]

    assert first_gen.best_fitness <= last_gen.best_fitness, "Best fitness must not decrease over generations"
    assert 0.0 <= last_gen.diversity <= 1.0, "Diversity index bounds error"

    print(f"Optimized Route Path: {' → '.join(opt.path_nodes)}")
    print(f"Optimal Distance: {opt.distance} miles, Cost: ${opt.cost}, Transit Time: {opt.transit_time} days")
    print(f"Best Fitness first gen: {first_gen.best_fitness} → last gen: {last_gen.best_fitness}")
    print(f"Convergence Generation: {payload.metadata.get('convergence_generation')}")
    print(f"Fitness Improvement: {payload.metadata.get('improvement_percentage')}%")
    print("✓ GA Evolution verified.")


def test_cache():
    """Validate GA cache hits return cached=True flags."""
    print("\n--- TESTING CACHE MECHANICS ---")
    GeneticAlgorithmEngine.clear_cache()
    from backend.services.graph_engine import GraphEngine
    graph = GraphEngine.get_graph_payload({})
    src = list(graph.neighbor_mapping.keys())[0]
    dest = graph.neighbor_mapping[src][0]["destination"]

    p1 = GeneticAlgorithmEngine.optimize_route(src, dest, {}, population_size=10, generations=5)
    assert p1.cached is False, "First run should miss cache"

    p2 = GeneticAlgorithmEngine.optimize_route(src, dest, {}, population_size=10, generations=5)
    assert p2.cached is True, "Second run should hit cache"

    print("✓ Cache verified.")


def test_invalid_nodes():
    """Verify GA handles non-existent node searches gracefully."""
    print("\n--- TESTING INVALID SEARCH ---")
    payload = GeneticAlgorithmEngine.optimize_route("UNKNOWN_SRC", "UNKNOWN_DEST", {})
    assert payload.optimized_route.is_feasible is False
    assert payload.optimized_route.fitness == 0.0001
    print("✓ Invalid searches verified.")


if __name__ == "__main__":
    print("Initializing Genetic Algorithm Optimization Engine verification suite...")
    setup()

    test_fitness_calculations()
    test_genetic_evolution()
    test_cache()
    test_invalid_nodes()

    print("\n" + "=" * 60)
    print("All Genetic Algorithm Optimization Engine tests passed successfully!")
    print("=" * 60)
