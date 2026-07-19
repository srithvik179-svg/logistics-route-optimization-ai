"""Verification test suite for the Network Optimization Readiness Engine (Phase 20).

Tests matrix indexing, normalized weights, graph validation, matrix generation, baselines,
metadata, cache hits, and filter subsetting.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.services.repository import repository
from backend.services.optimization_readiness_engine import OptimizationReadinessEngine
from backend.services.graph_preprocessor import GraphPreprocessor
from backend.services.constraint_validator import ConstraintValidator


def setup():
    """Initialize repository for tests."""
    if not repository.is_initialized():
        repository.initialize()
    OptimizationReadinessEngine.clear_cache()


def test_preprocessing():
    """Verify matrix indexing and normalization bounds."""
    print("\n--- TESTING PREPROCESSING ---")
    payload = OptimizationReadinessEngine.get_readiness_payload({})
    nodes = payload.nodes
    edges = payload.edges

    assert len(nodes) > 0, "Nodes registry must not be empty"
    assert len(edges) > 0, "Edges registry must not be empty"

    # Verify indices
    for idx, node in enumerate(nodes):
        assert node.matrix_index == idx, f"Matrix index mismatch at {node.node_id}"
        assert 0.0 <= node.normalized_score <= 1.0, "Node normalized score bounds error"

    for edge in edges:
        assert edge.source_index >= 0, "Source index must be non-negative"
        assert edge.destination_index >= 0, "Destination index must be non-negative"
        assert 0.0 <= edge.normalized_weight <= 1.0, "Edge normalized weight bounds error"

    print(f"Preprocessed Nodes Count: {len(nodes)}")
    print(f"Preprocessed Edges Count: {len(edges)}")
    print("✓ Preprocessing verified.")


def test_validation():
    """Verify validation warnings and negative weight flags."""
    print("\n--- TESTING GRAPH VALIDATION ---")
    payload = OptimizationReadinessEngine.get_readiness_payload({})
    val = payload.validation

    assert val.is_valid is True, "Graph must be valid for standard dataset"
    assert val.has_negative_weights is False, "Standard graph must not have negative weights"
    assert val.has_duplicate_edges is False, "Standard graph must not have duplicate edges"

    print(f"Graph is valid: {val.is_valid}")
    print(f"Disconnected sub-networks: {val.disconnected_components_count}")
    print(f"Validation warnings count: {len(val.warnings)}")
    print("✓ Graph validation verified.")


def test_matrices():
    """Verify dense 2D matrices generation."""
    print("\n--- TESTING DENSE MATRICES ---")
    payload = OptimizationReadinessEngine.get_readiness_payload({})
    n = len(payload.nodes)

    assert len(payload.distance_matrix) == n, "Distance matrix dimensions mismatch"
    assert len(payload.cost_matrix) == n, "Cost matrix dimensions mismatch"
    assert len(payload.transit_matrix) == n, "Transit matrix dimensions mismatch"
    assert len(payload.capacity_matrix) == n, "Capacity matrix dimensions mismatch"
    assert len(payload.sla_matrix) == n, "SLA matrix dimensions mismatch"

    # Self-loops must be 0
    for i in range(n):
        assert payload.distance_matrix[i][i] == 0.0, "Distance self-loop must be 0"
        assert payload.cost_matrix[i][i] == 0.0, "Cost self-loop must be 0"
        assert payload.transit_matrix[i][i] == 0.0, "Transit self-loop must be 0"

    print(f"Matrix Dimension: {n} x {n}")
    print("✓ Matrices verified.")


def test_baselines_and_constraints():
    """Verify baseline aggregates and constraints limits."""
    print("\n--- TESTING BASELINES & CONSTRAINTS ---")
    payload = OptimizationReadinessEngine.get_readiness_payload({})
    base = payload.baselines
    cons = payload.constraints

    assert base.baseline_cost > 0, "Baseline cost must be positive"
    assert base.baseline_transit_time > 0, "Baseline transit time must be positive"
    assert 0.0 <= base.baseline_capacity_utilization <= 1.0, "Baseline utilization fraction bounds error"
    assert base.baseline_sla_compliance > 0, "Baseline SLA compliance must be positive"

    assert cons.max_distance_limit > 0, "Constraint max distance must be positive"
    assert cons.max_cost_limit > 0, "Constraint max cost must be positive"

    print(f"Baseline Cost: ${base.baseline_cost}")
    print(f"Baseline Transit Time: {base.baseline_transit_time} days")
    print(f"Baseline SLA Compliance: {base.baseline_sla_compliance}%")
    print(f"Max distance constraint limit: {cons.max_distance_limit} miles")
    print("✓ Baselines & Constraints verified.")


def test_cache():
    """Validate cache hits return payload with cached=True flag."""
    print("\n--- TESTING CACHE MECHANICS ---")
    OptimizationReadinessEngine.clear_cache()

    p1 = OptimizationReadinessEngine.get_readiness_payload({})
    assert p1.cached is False, "First payload fetch should miss cache"

    p2 = OptimizationReadinessEngine.get_readiness_payload({})
    assert p2.cached is True, "Second payload fetch should hit cache"

    assert len(p1.nodes) == len(p2.nodes), "Payload nodes count must match"
    print("✓ Caching validated.")


def test_filtered_analytics():
    """Validate filter subsetting reduces metrics correctly."""
    print("\n--- TESTING FILTERED SUBSETTING ---")
    OptimizationReadinessEngine.clear_cache()

    full = OptimizationReadinessEngine.get_readiness_payload({})

    OptimizationReadinessEngine.clear_cache()
    filtered = OptimizationReadinessEngine.get_readiness_payload({"partner": "Swift Logico"})

    assert len(filtered.nodes) == len(full.nodes), "Nodes list size must remain same"
    assert len(filtered.edges) <= len(full.edges), "Filtered edges count must be smaller or equal"
    print(f"Full edges: {len(full.edges)}")
    print(f"Filtered edges: {len(filtered.edges)}")
    print("✓ Filter subsetting validated.")


if __name__ == "__main__":
    print("Initializing Network Optimization Readiness Engine verification suite...")
    setup()

    test_preprocessing()
    test_validation()
    test_matrices()
    test_baselines_and_constraints()
    test_cache()
    test_filtered_analytics()

    print("\n" + "=" * 60)
    print("All Network Optimization Readiness Engine tests passed successfully!")
    print("=" * 60)
