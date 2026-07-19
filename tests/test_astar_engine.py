"""Verification test suite for the A* Pathfinding Engine (Phase 21).

Tests optimal route distance/cost/transit time properties, priority queue tie-breakers,
multiple heuristics, performance metrics, expansions statistics, and cache.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.services.repository import repository
from backend.services.astar_engine import AStarEngine
from backend.services.priority_queue import AStarPriorityQueue
from backend.services.heuristic_service import HeuristicService


def setup():
    """Initialize repository for tests."""
    if not repository.is_initialized():
        repository.initialize()
    AStarEngine.clear_cache()


def test_priority_queue():
    """Verify priority queue insertion ordering and tie-breaker counter logic."""
    print("\n--- TESTING PRIORITY QUEUE ---")
    pq = AStarPriorityQueue()
    pq.push("node_a", 10.5)
    pq.push("node_b", 5.0)
    pq.push("node_c", 5.0)  # Same f-score priority to trigger tie-breaker

    assert pq.size() == 3, "Queue size must be 3"
    
    p1, n1 = pq.pop()
    assert n1 == "node_b", "First popped should be node_b"
    assert p1 == 5.0

    p2, n2 = pq.pop()
    assert n2 == "node_c", "Second popped should be node_c (index insertion tie-breaker)"
    assert p2 == 5.0

    p3, n3 = pq.pop()
    assert n3 == "node_a", "Third popped should be node_a"
    assert p3 == 10.5

    assert pq.is_empty() is True
    print("✓ Priority Queue verified.")


def test_astar_search():
    """Verify single path search and reconstructed path metrics."""
    print("\n--- TESTING A* PATH SEARCH ---")
    payload = AStarEngine.get_astar_payload({})
    assert len(payload.paths) > 0, "Calculated paths must not be empty"

    # Select a source node and destination node
    src = list(payload.paths.keys())[0]
    dest = list(payload.paths[src].keys())[0]

    path_res = payload.paths[src][dest]
    assert path_res.source == src
    assert path_res.destination == dest
    assert len(path_res.path_nodes) >= 2, "Path must contain at least source and destination"
    assert path_res.total_distance > 0, "Distance must be positive"
    assert path_res.total_cost > 0, "Cost must be positive"
    assert path_res.total_transit_time > 0, "Transit time must be positive"
    assert path_res.hops == len(path_res.path_nodes) - 1

    print(f"Path computed: {' → '.join(path_res.path_nodes)}")
    print(f"Distance: {path_res.total_distance} miles, Cost: ${path_res.total_cost}, Time: {path_res.total_transit_time} days")
    print(f"Expansions: {path_res.search_expansion_count}, Visited: {path_res.visited_nodes_count}, Explored: {path_res.explored_nodes_count}")
    print("✓ Path metrics verified.")


def test_heuristics():
    """Verify multiple heuristics computations and metrics."""
    print("\n--- TESTING HEURISTICS ---")
    heuristics = ["great-circle", "weighted", "transit", "cost", "composite"]

    for h in heuristics:
        payload = AStarEngine.get_astar_payload({}, heuristic_type=h)
        assert len(payload.heuristics_performance) > 0
        perf = payload.heuristics_performance[0]
        assert perf.heuristic_type == h
        assert perf.computation_time_ms >= 0.0
        print(f"Heuristic '{h}' -> Average Absolute Error: {perf.average_error} miles")

    print("✓ Heuristics verified.")


def test_cache():
    """Validate that query cache returns cached=True flags on hits."""
    print("\n--- TESTING CACHE MECHANICS ---")
    AStarEngine.clear_cache()

    p1 = AStarEngine.get_astar_payload({}, heuristic_type="great-circle")
    assert p1.cached is False, "First call should miss cache"

    p2 = AStarEngine.get_astar_payload({}, heuristic_type="great-circle")
    assert p2.cached is True, "Second call should hit cache"

    print("✓ Cache verified.")


def test_invalid_routes():
    """Verify error handling when searching paths for non-existent nodes."""
    print("\n--- TESTING INVALID ROUTES ---")
    # Query with non-existent IDs
    res = AStarEngine.find_path([], {}, {}, "UNKNOWN_SRC", "UNKNOWN_DEST", "great-circle")
    assert res is not None
    assert res.path_nodes == []
    assert res.total_distance == 999999.0
    assert res.total_cost == 999999.0
    assert res.total_transit_time == 999999.0
    print("✓ Invalid routes verified.")


if __name__ == "__main__":
    print("Initializing A* Pathfinding Engine verification suite...")
    setup()

    test_priority_queue()
    test_astar_search()
    test_heuristics()
    test_cache()
    test_invalid_routes()

    print("\n" + "=" * 60)
    print("All A* Pathfinding Engine tests passed successfully!")
    print("=" * 60)
