"""Verification test suite for the Shortest Path Analytics Engine (Phase 18).

Tests Dijkstra routing calculations, BFS hops sequences, DFS explorations,
network accessibility maps, search statistics benchmarks, cache hits, and filter subsetting.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.services.repository import repository
from backend.services.shortest_path_engine import ShortestPathEngine
from backend.services.dijkstra_service import DijkstraService
from backend.services.traversal_services import TraversalService
from backend.services.graph_engine import GraphEngine


def setup():
    """Initialize repository for tests."""
    if not repository.is_initialized():
        repository.initialize()
    ShortestPathEngine.clear_cache()


def test_dijkstra_algorithm():
    """Verify Dijkstra algorithm paths calculations."""
    print("\n--- TESTING DIJKSTRA PATHFINDING ---")
    payload = ShortestPathEngine.get_shortest_path_payload({})
    paths = payload.shortest_paths

    assert len(paths) > 0, "Shortest paths dict must not be empty"

    # Find a valid path
    valid_path = None
    for src, targets in paths.items():
        for dest, path in targets.items():
            if path and len(path.path_nodes) > 1:
                valid_path = path
                break
        if valid_path:
            break

    assert valid_path is not None, "At least one valid path sequence must exist"
    assert valid_path.total_distance >= 0, "Distance must be non-negative"
    assert valid_path.total_cost >= 0, "Cost must be non-negative"
    assert valid_path.total_transit_time >= 0, "Transit time must be non-negative"
    assert valid_path.hops == len(valid_path.path_nodes) - 1, "Hops count mismatch"

    # Test direct Dijkstra execution
    graph = GraphEngine.get_graph_payload({})
    nodes = [n.node_id for n in graph.nodes]
    neighbor_map = graph.neighbor_mapping
    dist_weight = lambda edge: float(edge.get("distance", 0.0))

    direct_res = DijkstraService.find_shortest_path(nodes, neighbor_map, valid_path.source, valid_path.destination, dist_weight)
    assert direct_res is not None, "Direct Dijkstra calculation must succeed"
    assert direct_res.total_distance == valid_path.total_distance, "Distance values must match"

    print(f"Shortest path from {valid_path.source} to {valid_path.destination}: {valid_path.path_nodes}")
    print(f"Distance: {valid_path.total_distance} miles, Cost: ${valid_path.total_cost}, Time: {valid_path.total_transit_time} days")
    print("✓ Dijkstra pathfinding verified.")


def test_bfs_dfs_traversals():
    """Verify BFS hops sequence and DFS explorations."""
    print("\n--- TESTING BFS & DFS TRAVERSALS ---")
    graph = GraphEngine.get_graph_payload({})
    nodes = [n.node_id for n in graph.nodes]
    neighbor_map = graph.neighbor_mapping

    # Find a pair with a multi-hop path
    src, dest = "HUB-A", "HUB-B"

    # BFS Minimum Hops
    bfs_res = TraversalService.find_path_bfs(neighbor_map, src, dest)
    # DFS Path
    dfs_res = TraversalService.find_path_dfs(neighbor_map, src, dest)

    if bfs_res:
        assert len(bfs_res.path_nodes) >= 2, "Path must have at least 2 nodes"
        assert bfs_res.hops == len(bfs_res.path_nodes) - 1, "Hops mismatch"
        print(f"BFS Path from {src} to {dest}: {bfs_res.path_nodes} (Hops: {bfs_res.hops})")
    
    if dfs_res:
        assert len(dfs_res.path_nodes) >= 2, "Path must have at least 2 nodes"
        print(f"DFS Path from {src} to {dest}: {dfs_res.path_nodes}")

    print("✓ BFS and DFS traversals verified.")


def test_accessibility_metrics():
    """Verify reachable and unreachable node lists."""
    print("\n--- TESTING NETWORK ACCESSIBILITY ---")
    payload = ShortestPathEngine.get_shortest_path_payload({})
    acc = payload.accessibility

    assert len(acc.reachable_nodes) > 0, "Reachable nodes map must not be empty"
    assert len(acc.unreachable_nodes) > 0, "Unreachable nodes map must not be empty"
    assert len(acc.highly_accessible_hubs) > 0, "Highly accessible hubs must not be empty"
    assert len(acc.least_accessible_hubs) > 0, "Least accessible hubs must not be empty"

    first_node = list(acc.reachable_nodes.keys())[0]
    print(f"Reachable from {first_node}: {acc.reachable_nodes[first_node]}")
    print(f"Unreachable from {first_node}: {acc.unreachable_nodes[first_node]}")
    print(f"Highly Accessible Hubs: {acc.highly_accessible_hubs}")
    print(f"Least Accessible Hubs: {acc.least_accessible_hubs}")
    print("✓ Accessibility metrics verified.")


def test_statistics():
    """Verify routing performance and search benchmarks stats."""
    print("\n--- TESTING SEARCH BENCHMARKS ---")
    payload = ShortestPathEngine.get_shortest_path_payload({})
    st = payload.statistics

    assert st.total_calculations > 0, "Total calculations count must be positive"
    assert st.average_search_time_ms >= 0, "Average search time must be non-negative"
    assert st.average_path_length >= 0, "Average path length must be non-negative"
    assert st.max_path_length >= st.min_path_length, "Max path length must be >= min"

    print(f"Total calculations: {st.total_calculations}")
    print(f"Avg Search Time: {st.average_search_time_ms} ms")
    print(f"Avg Path Length: {st.average_path_length} nodes")
    print(f"Max Path Length: {st.max_path_length} nodes, Min: {st.min_path_length} nodes")
    print("✓ Search statistics benchmarks verified.")


def test_cache():
    """Validate cache hits return payload with cached=True flag."""
    print("\n--- TESTING CACHE MECHANICS ---")
    ShortestPathEngine.clear_cache()

    p1 = ShortestPathEngine.get_shortest_path_payload({})
    assert p1.cached is False, "First payload fetch should miss cache"

    p2 = ShortestPathEngine.get_shortest_path_payload({})
    assert p2.cached is True, "Second payload fetch should hit cache"

    assert p1.statistics.total_calculations == p2.statistics.total_calculations, "Payload calculations count must match"
    print("✓ Caching validated.")


def test_filtered_analytics():
    """Validate filter subsetting reduces paths correctly."""
    print("\n--- TESTING FILTERED SUBSETTING ---")
    ShortestPathEngine.clear_cache()

    full = ShortestPathEngine.get_shortest_path_payload({})

    ShortestPathEngine.clear_cache()
    filtered = ShortestPathEngine.get_shortest_path_payload({"partner": "Swift Logico"})

    assert filtered.statistics.total_calculations <= full.statistics.total_calculations, "Filtered path calculations count must be smaller or equal"
    print(f"Full path calculations count: {full.statistics.total_calculations}")
    print(f"Filtered path calculations count: {filtered.statistics.total_calculations}")
    print("✓ Filter subsetting validated.")


if __name__ == "__main__":
    print("Initializing Shortest Path Analytics Engine verification suite...")
    setup()

    test_dijkstra_algorithm()
    test_bfs_dfs_traversals()
    test_accessibility_metrics()
    test_statistics()
    test_cache()
    test_filtered_analytics()

    print("\n" + "=" * 60)
    print("All Shortest Path Analytics Engine tests passed successfully!")
    print("=" * 60)
