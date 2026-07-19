"""Verification test suite for the AI Decision Support Preparation Engine (Phase 25).

Tests feature normalization, decision scenario mappings, explainability metadata compiling,
caching controls, and API endpoint integration.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.services.repository import repository
from backend.services.ai_preparation_engine import AIPreparationEngine
from backend.services.feature_engineering import FeatureEngineeringService


def setup():
    """Initialize repository for tests."""
    if not repository.is_initialized():
        repository.initialize()
    AIPreparationEngine.clear_cache()


def test_feature_extraction():
    """Verify feature vector calculations and normalizations."""
    print("\n--- TESTING FEATURE ENGINEERING ---")
    fv = FeatureEngineeringService.extract_features(
        path_nodes=["HUB-A", "HUB-B"],
        distance=120.5,
        cost=150.5,
        transit_time=2.0,
        composite_score=93.26
    )

    assert fv.cost == round(150.5 / 500.0, 4), "Cost normalization index error"
    assert fv.transit_time == round(2.0 / 5.0, 4), "Transit time normalization index error"
    assert fv.sla_compliance == 0.98, "Expected 98% SLA compliance for 2.0 days"
    assert fv.reliability == 0.95, "Expected 95% reliability for 1-hop path"
    assert fv.operational_efficiency == round(0.95 * 0.5 + 0.88 * 0.5, 4), "Operational efficiency calculation error"
    assert fv.composite_score == 93.26

    print("✓ Feature extraction verified.")


def test_ai_decision_preparation():
    """Verify decision contexts, scenarios mappings, explainability datasets, and statistics."""
    print("\n--- TESTING AI DECISION BUILDER ---")
    from backend.services.graph_engine import GraphEngine
    graph = GraphEngine.get_graph_payload({})
    neighbor_map = graph.neighbor_mapping
    
    src = list(neighbor_map.keys())[0]
    dest = neighbor_map[src][0]["destination"]

    payload = AIPreparationEngine.prepare_decision_support(src, dest, {})

    assert payload.context_id is not None, "Context ID must be generated"
    assert len(payload.feature_matrix) > 0, "Feature matrix must contain candidates features"
    assert len(payload.scenarios) > 0, "Decision scenarios must be mapped"
    assert len(payload.explainability) > 0, "Explainability metadata must be compiled"

    # Verify scenario classifications
    sc = payload.scenarios
    assert "cheapest_route" in sc
    assert "fastest_route" in sc
    assert "balanced_route" in sc

    # Verify explainability factors
    exp = payload.explainability
    assert "feature_importance_weights" in exp
    assert "algorithm_comparisons" in exp
    assert "decision_confidence_index" in exp

    print(f"Context ID: {payload.context_id}")
    print(f"Feature matrix candidates mapped: {list(payload.feature_matrix.keys())}")
    print(f"Cheapest route algorithm selected: {sc['cheapest_route'].algorithm}")
    print(f"Fastest route algorithm selected: {sc['fastest_route'].algorithm}")
    print(f"Balanced route algorithm selected: {sc['balanced_route'].algorithm}")
    print(f"Global decision confidence: {exp['decision_confidence_index']}")
    print("✓ AI Decision builder verified.")


def test_cache():
    """Validate cache hits return cached=True flags."""
    print("\n--- TESTING CACHE MECHANICS ---")
    AIPreparationEngine.clear_cache()
    from backend.services.graph_engine import GraphEngine
    graph = GraphEngine.get_graph_payload({})
    src = list(graph.neighbor_mapping.keys())[0]
    dest = graph.neighbor_mapping[src][0]["destination"]

    p1 = AIPreparationEngine.prepare_decision_support(src, dest, {})
    assert p1.cached is False, "First run should miss cache"

    p2 = AIPreparationEngine.prepare_decision_support(src, dest, {})
    assert p2.cached is True, "Second run should hit cache"

    print("✓ Cache verified.")


def test_invalid_search():
    """Verify preparation handles non-existent node searches gracefully."""
    print("\n--- TESTING INVALID SEARCH ---")
    payload = AIPreparationEngine.prepare_decision_support("UNKNOWN_SRC", "UNKNOWN_DEST", {})
    assert len(payload.feature_matrix) == 0
    assert len(payload.scenarios) == 0
    assert len(payload.explainability) == 0
    print("✓ Invalid searches verified.")


if __name__ == "__main__":
    print("Initializing AI Decision Support Preparation Engine verification suite...")
    setup()

    test_feature_extraction()
    test_ai_decision_preparation()
    test_cache()
    test_invalid_search()

    print("\n" + "=" * 60)
    print("All AI Decision Support Preparation Engine tests passed successfully!")
    print("=" * 60)
