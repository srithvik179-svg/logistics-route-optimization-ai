"""Verification test suite for the Route Graph Engine (Phase 16).

Tests node and edge formats, adjacency lists, adjacency matrices, neighbor mappings,
graph overview statistics, connectivity analysis (bridges, hubs, dead-ends), caching, and filters.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.services.repository import repository
from backend.services.graph_engine import GraphEngine


def setup():
    """Initialize repository for tests."""
    if not repository.is_initialized():
        repository.initialize()
    GraphEngine.clear_cache()


def test_nodes_and_edges():
    """Validate nodes and edges lists format."""
    print("\n--- TESTING GRAPH NODES & EDGES ---")
    payload = GraphEngine.get_graph_payload({})
    nodes = payload.nodes
    edges = payload.edges

    assert len(nodes) > 0, "Graph nodes list must not be empty"
    assert len(edges) > 0, "Graph edges list must not be empty"

    # Verify a node structure
    first_node = nodes[0]
    assert len(first_node.node_id) > 0, "Node ID must not be empty"
    assert len(first_node.name) > 0, "Node name must not be empty"
    assert first_node.node_type in ["Hub", "Repair Center", "Warehouse", "Distribution Center"], "Invalid node type"
    assert first_node.capacity > 0, "Node capacity must be positive"

    # Verify an edge structure
    first_edge = edges[0]
    assert len(first_edge.source) > 0, "Edge source must not be empty"
    assert len(first_edge.destination) > 0, "Edge destination must not be empty"
    assert first_edge.distance > 0, "Edge distance must be positive"
    assert first_edge.transit_time >= 0, "Edge transit time must be non-negative"
    assert first_edge.cost >= 0, "Edge cost must be non-negative"
    assert first_edge.volume >= 0, "Edge volume must be non-negative"
    assert first_edge.capacity > 0, "Edge capacity must be positive"
    assert first_edge.status in ["Active", "Congested", "Disrupted"], "Invalid edge status"
    assert len(first_edge.logistics_partner) > 0, "Edge partner must not be empty"

    print(f"Total Nodes: {len(nodes)}")
    print(f"Total Edges: {len(edges)}")
    print(f"First Node: {first_node.model_dump()}")
    print(f"First Edge: {first_edge.model_dump()}")
    print("✓ Nodes and Edges validated.")


def test_adjacency_structures():
    """Validate adjacency structures, matrix weights, neighbors mapping, and shortest path weights."""
    print("\n--- TESTING ADJACENCY STRUCTURES ---")
    payload = GraphEngine.get_graph_payload({})
    adj_list = payload.adjacency_list
    adj_matrix = payload.adjacency_matrix
    neighbor_map = payload.neighbor_mapping
    weighted_routes = payload.weighted_route_list

    assert len(adj_list) == len(payload.nodes), "Adjacency list size must equal nodes count"
    assert len(adj_matrix) == len(payload.nodes), "Adjacency matrix rows must equal nodes count"
    assert len(neighbor_map) == len(payload.nodes), "Neighbor mapping size must equal nodes count"
    assert len(weighted_routes) == len(payload.edges), "Weighted routes list size must equal edges count"

    # Verify neighbors list details
    first_node_id = payload.nodes[0].node_id
    neighbors = adj_list[first_node_id]
    assert isinstance(neighbors, list), "Adjacency neighbors must be a list"

    # Verify matrix value lookup
    for edge in payload.edges:
        assert adj_matrix[edge.source][edge.destination] == edge.distance, "Matrix weight must equal edge distance"

    # Verify weighted route weights
    first_route = weighted_routes[0]
    assert first_route.weight_distance > 0, "Weight distance must be positive"
    assert first_route.weight_cost >= 0, "Weight cost must be non-negative"
    assert first_route.weight_time >= 0, "Weight time must be non-negative"

    print(f"Adjacency neighbors for {first_node_id}: {neighbors}")
    print(f"Matrix weight from {first_route.source} to {first_route.destination}: {adj_matrix[first_route.source][first_route.destination]}")
    print("✓ Adjacency structures validated.")


def test_statistics():
    """Validate network topology statistics."""
    print("\n--- TESTING GRAPH TOPOLOGY STATISTICS ---")
    payload = GraphEngine.get_graph_payload({})
    st = payload.statistics

    assert st.total_nodes == len(payload.nodes), "Nodes count mismatch"
    assert st.total_edges == len(payload.edges), "Edges count mismatch"
    assert st.avg_node_degree >= 0, "Avg degree must be non-negative"
    assert st.max_degree >= st.min_degree, "Max degree must be >= min degree"
    assert st.connected_components >= 1, "Connected components must be >= 1"
    assert st.isolated_nodes >= 0, "Isolated nodes count must be non-negative"
    assert 0.0 <= st.graph_density <= 1.0, "Graph density must be in 0-1 bounds"
    assert st.avg_route_length >= 0, "Avg route length must be non-negative"

    print(f"Avg Node Degree: {st.avg_node_degree}")
    print(f"Max Degree: {st.max_degree}, Min Degree: {st.min_degree}")
    print(f"Connected Components: {st.connected_components}")
    print(f"Isolated Nodes: {st.isolated_nodes}")
    print(f"Graph Density: {st.graph_density}")
    print(f"Avg Route Length: {st.avg_route_length} miles")
    print("✓ Statistics validated.")


def test_connectivity():
    """Validate connectivity analysis output (dead-ends, bridges, etc.)."""
    print("\n--- TESTING CONNECTIVITY ANALYSIS ---")
    payload = GraphEngine.get_graph_payload({})
    cn = payload.connectivity

    assert isinstance(cn.disconnected_networks, list), "disconnected_networks must be a list"
    assert isinstance(cn.dead_end_nodes, list), "dead_end_nodes must be a list"
    assert isinstance(cn.highly_connected_hubs, list), "highly_connected_hubs must be a list"
    assert isinstance(cn.critical_connections, list), "critical_connections must be a list"
    assert isinstance(cn.bridge_routes, list), "bridge_routes must be a list"

    print(f"Disconnected Networks subsets count: {len(cn.disconnected_networks)}")
    print(f"Dead-end nodes: {cn.dead_end_nodes}")
    print(f"Highly connected hubs: {cn.highly_connected_hubs}")
    print(f"Critical connections: {cn.critical_connections}")
    print(f"Bridge routes: {cn.bridge_routes}")
    print("✓ Connectivity analysis validated.")


def test_cache():
    """Validate cache hits return payload with cached=True flag."""
    print("\n--- TESTING CACHE MECHANICS ---")
    GraphEngine.clear_cache()

    p1 = GraphEngine.get_graph_payload({})
    assert p1.cached is False, "First payload fetch should miss cache"

    p2 = GraphEngine.get_graph_payload({})
    assert p2.cached is True, "Second payload fetch should hit cache"

    assert p1.statistics.total_nodes == p2.statistics.total_nodes, "Payload nodes count must match"
    print("✓ Caching validated.")


def test_filtered_analytics():
    """Validate filter subsetting reduces graph elements correctly."""
    print("\n--- TESTING FILTERED SUBSETTING ---")
    GraphEngine.clear_cache()

    full = GraphEngine.get_graph_payload({})

    GraphEngine.clear_cache()
    filtered = GraphEngine.get_graph_payload({"partner": "Swift LogiCo"})

    assert len(filtered.edges) <= len(full.edges), "Filtered edges count must be smaller or equal"

    print(f"Unfiltered routes: {len(full.edges)}")
    print(f"Filtered routes: {len(filtered.edges)}")
    print("✓ Filter subsetting validated.")


if __name__ == "__main__":
    print("Initializing Route Graph Engine verification suite...")
    setup()

    test_nodes_and_edges()
    test_adjacency_structures()
    test_statistics()
    test_connectivity()
    test_cache()
    test_filtered_analytics()

    print("\n" + "=" * 60)
    print("All Route Graph Engine tests passed successfully!")
    print("=" * 60)
