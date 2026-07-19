"""Verification test suite for the Ant Colony Optimization Engine (Phase 23).

Tests pheromone evaporation/deposits, transition probabilities, path constructions,
iteration stats compiling, algorithm benchmarking, and caching layers.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.services.repository import repository
from backend.services.ant_colony_engine import AntColonyEngine
from backend.services.pheromone_manager import PheromoneManager


def setup():
    """Initialize repository for tests."""
    if not repository.is_initialized():
        repository.initialize()
    AntColonyEngine.clear_cache()


def test_pheromone_evaporation():
    """Verify pheromone evaporation bounds check."""
    print("\n--- TESTING PHEROMONE EVAPORATION ---")
    # Get standard graph neighbor map
    from backend.services.graph_engine import GraphEngine
    graph = GraphEngine.get_graph_payload({})
    nodes = [n.node_id for n in graph.nodes]
    neighbor_map = graph.neighbor_mapping

    pm = PheromoneManager(nodes, neighbor_map, initial_level=1.0)
    
    # Select an active edge
    u = list(pm.matrix.keys())[0]
    v = list(pm.matrix[u].keys())[0]

    assert pm.matrix[u][v] == 1.0, "Initial level must be 1.0"
    
    pm.evaporate(rho=0.20)
    assert pm.matrix[u][v] == 0.80, "Pheromone must evaporate by 20% to 0.80"

    print("✓ Pheromone evaporation verified.")


def test_aco_evolution():
    """Verify swarm routing optimization and iteration stats compiling."""
    print("\n--- TESTING ACO SWARM LOOP ---")
    from backend.services.graph_engine import GraphEngine
    graph = GraphEngine.get_graph_payload({})
    neighbor_map = graph.neighbor_mapping
    
    src = list(neighbor_map.keys())[0]
    dest = neighbor_map[src][0]["destination"]

    payload = AntColonyEngine.optimize_route(
        src, dest, {}, swarm_size=10, iterations=5
    )

    assert payload.optimized_route is not None, "Swarm optimization must return a solution"
    assert len(payload.iteration_history) > 0, "Iteration history must be recorded"
    assert payload.pheromone_matrix is not None, "Final pheromone matrix must be compiled"

    opt = payload.optimized_route
    assert opt.fitness > 0
    assert len(opt.path_nodes) >= 2
    assert opt.path_nodes[0] == src
    assert opt.path_nodes[-1] == dest

    # Check stats ranges
    first_it = payload.iteration_history[0]
    last_it = payload.iteration_history[-1]
    assert first_it.best_fitness <= last_it.best_fitness, "Best fitness must not decrease"

    print(f"Optimized path nodes: {' → '.join(opt.path_nodes)}")
    print(f"Optimal Distance: {opt.distance} miles, Cost: ${opt.cost}, Time: {opt.transit_time} days")
    print(f"Best Fitness first iteration: {first_it.best_fitness} → last iteration: {last_it.best_fitness}")
    print("✓ ACO Swarm Loop verified.")


def test_benchmarks():
    """Verify algorithm benchmarking outputs (Dijkstra, A*, GA, ACO comparison)."""
    print("\n--- TESTING ROUTING BENCHMARKS ---")
    from backend.services.graph_engine import GraphEngine
    graph = GraphEngine.get_graph_payload({})
    src = list(graph.neighbor_mapping.keys())[0]
    dest = graph.neighbor_mapping[src][0]["destination"]

    payload = AntColonyEngine.optimize_route(src, dest, {}, swarm_size=10, iterations=5)
    benchmarks = payload.benchmarks

    assert len(benchmarks) > 0, "Benchmarks must not be empty"
    algorithms = [b.algorithm for b in benchmarks]

    assert "Dijkstra" in algorithms, "Benchmarks must contain Dijkstra comparison"
    assert "A*" in algorithms, "Benchmarks must contain A* comparison"
    assert "Genetic Algorithm" in algorithms, "Benchmarks must contain GA comparison"
    assert "Ant Colony Optimization" in algorithms, "Benchmarks must contain ACO comparison"

    for b in benchmarks:
        assert b.distance > 0, f"Distance must be positive for {b.algorithm}"
        assert b.cost > 0, f"Cost must be positive for {b.algorithm}"
        assert b.transit_time > 0, f"Transit time must be positive for {b.algorithm}"
        print(f"Algorithm '{b.algorithm}' -> Cost: ${b.cost}, Time: {b.transit_time} days, Hops: {b.hops}, Time: {b.execution_time_ms} ms")

    print("✓ Algorithm benchmarking verified.")


def test_cache():
    """Validate GA cache hits return cached=True flags."""
    print("\n--- TESTING CACHE MECHANICS ---")
    AntColonyEngine.clear_cache()
    from backend.services.graph_engine import GraphEngine
    graph = GraphEngine.get_graph_payload({})
    src = list(graph.neighbor_mapping.keys())[0]
    dest = graph.neighbor_mapping[src][0]["destination"]

    p1 = AntColonyEngine.optimize_route(src, dest, {}, swarm_size=10, iterations=5)
    assert p1.cached is False, "First run should miss cache"

    p2 = AntColonyEngine.optimize_route(src, dest, {}, swarm_size=10, iterations=5)
    assert p2.cached is True, "Second run should hit cache"

    print("✓ Cache verified.")


def test_invalid_nodes():
    """Verify GA handles non-existent node searches gracefully."""
    print("\n--- TESTING INVALID SEARCH ---")
    payload = AntColonyEngine.optimize_route("UNKNOWN_SRC", "UNKNOWN_DEST", {})
    assert payload.optimized_route.is_feasible is False
    assert payload.optimized_route.fitness == 0.0001
    print("✓ Invalid searches verified.")


if __name__ == "__main__":
    print("Initializing Ant Colony Optimization Engine verification suite...")
    setup()

    test_pheromone_evaporation()
    test_aco_evolution()
    test_benchmarks()
    test_cache()
    test_invalid_nodes()

    print("\n" + "=" * 60)
    print("All Ant Colony Optimization Engine tests passed successfully!")
    print("=" * 60)
