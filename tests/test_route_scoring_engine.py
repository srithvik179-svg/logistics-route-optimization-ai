"""Verification test suite for the Route Cost & Scoring Engine (Phase 19).

Tests individual normalized scores, composite index calculations, rankings sorting lists,
correlation comparisons, statistics aggregates, business insights, caching, and filter subsetting.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.services.repository import repository
from backend.services.route_scoring_engine import RouteScoringEngine
from backend.services.route_score_calculator import RouteScoreCalculator


def setup():
    """Initialize repository for tests."""
    if not repository.is_initialized():
        repository.initialize()
    RouteScoringEngine.clear_cache()


def test_individual_normalization():
    """Verify individual parameter normalization behaves correctly."""
    print("\n--- TESTING INDIVIDUAL SCORE NORMALIZATION ---")
    # Low distance, low cost, low time -> High scores
    res1 = RouteScoreCalculator.calculate_scores(
        "HUB-A", "HUB-B",
        distance=60.0, cost=50.0, transit_time=0.5,
        volume=100.0, capacity=1000.0, partner_rating=5.0, sla_compliance=100.0
    )
    assert res1.distance_score > 80.0, "Short distance must produce high score"
    assert res1.cost_score > 80.0, "Low cost must produce high score"
    assert res1.transit_time_score > 80.0, "Fast time must produce high score"
    assert res1.sla_score == 100.0, "SLA compliance must equal 100"
    assert res1.partner_reliability_score == 100.0, "5 star rating must equal 100"

    # High distance, high cost, high time -> Low scores
    res2 = RouteScoreCalculator.calculate_scores(
        "HUB-A", "HUB-B",
        distance=600.0, cost=500.0, transit_time=5.0,
        volume=950.0, capacity=1000.0, partner_rating=1.0, sla_compliance=0.0
    )
    assert res2.distance_score == 0.0, "600mi distance must produce 0 score"
    assert res2.cost_score == 0.0, "$500 cost must produce 0 score"
    assert res2.transit_time_score == 0.0, "5d time must produce 0 score"
    assert res2.sla_score == 0.0, "SLA compliance must equal 0"
    assert res2.partner_reliability_score == 20.0, "1 star rating must equal 20"

    print("✓ Score normalization verified.")


def test_composite_calculations():
    """Verify composite index calculations and risk values."""
    print("\n--- TESTING COMPOSITE INDEX CALCULATIONS ---")
    res = RouteScoreCalculator.calculate_scores(
        "HUB-A", "HUB-B",
        distance=120.0, cost=150.0, transit_time=1.5,
        volume=650.0, capacity=1000.0, partner_rating=4.5, sla_compliance=98.0
    )

    assert 0.0 <= res.overall_route_score <= 100.0, "Overall score must be in 0-100 bounds"
    assert 0.0 <= res.business_priority_score <= 100.0, "Business priority must be in 0-100 bounds"
    assert 0.0 <= res.operational_risk_score <= 100.0, "Operational risk must be in 0-100 bounds"
    assert 0.0 <= res.performance_index <= 100.0, "Performance index must be in 0-100 bounds"
    assert res.composite_logistics_score == res.overall_route_score, "Composite logistics score must match overall route score"

    print(f"Overall Score: {res.overall_route_score}")
    print(f"Business Priority: {res.business_priority_score}")
    print(f"Operational Risk: {res.operational_risk_score}")
    print(f"Performance Index: {res.performance_index}")
    print("✓ Composite calculations verified.")


def test_rankings():
    """Verify route rankings set size and contents."""
    print("\n--- TESTING ROUTE RANKINGS SET ---")
    payload = RouteScoringEngine.get_route_scoring_payload({})
    rn = payload.rankings

    assert len(payload.route_scores) > 0, "Scores list must not be empty"
    assert len(rn.best_routes) > 0, "Best routes list must not be empty"
    assert len(rn.lowest_cost) > 0, "Lowest cost routes list must not be empty"
    assert len(rn.fastest) > 0, "Fastest routes list must not be empty"
    assert len(rn.most_reliable) > 0, "Most reliable routes list must not be empty"
    assert len(rn.highest_capacity) > 0, "Highest capacity routes list must not be empty"
    assert len(rn.highest_performing) > 0, "Highest performing routes list must not be empty"
    assert len(rn.worst_performing) > 0, "Worst performing routes list must not be empty"

    print(f"Top 3 Best Routes: {rn.best_routes[:3]}")
    print(f"Top 3 Fastest Routes: {rn.fastest[:3]}")
    print(f"Top 3 Lowest Cost: {rn.lowest_cost[:3]}")
    print("✓ Rankings verified.")


def test_comparisons_and_insights():
    """Verify strategy comparisons and business insights."""
    print("\n--- TESTING COMPARISONS & INSIGHTS ---")
    payload = RouteScoringEngine.get_route_scoring_payload({})
    comp = payload.comparisons
    ins = payload.business_insights

    assert "Distance vs Transit Time" in comp, "Missing distance vs transit comparison"
    assert "Cost vs Performance" in comp, "Missing cost vs performance comparison"
    
    pair_dt = comp["Distance vs Transit Time"]
    assert -1.0 <= pair_dt.correlation_coefficient <= 1.0, "Correlation coefficient bounds error"
    assert len(pair_dt.differences_summary) > 0, "Differences summary description missing"

    assert "expensive_routes" in ins, "Missing expensive routes insight"
    assert "low_performing_routes" in ins, "Missing low performing routes insight"
    assert "critical_routes" in ins, "Missing critical routes insight"

    print(f"Distance vs Transit Time correlation: {pair_dt.correlation_coefficient}")
    print(f"Expensive Routes Count: {len(ins['expensive_routes'])}")
    print(f"Critical Routes Count: {len(ins['critical_routes'])}")
    print("✓ Comparisons and insights verified.")


def test_cache():
    """Validate cache hits return payload with cached=True flag."""
    print("\n--- TESTING CACHE MECHANICS ---")
    RouteScoringEngine.clear_cache()

    p1 = RouteScoringEngine.get_route_scoring_payload({})
    assert p1.cached is False, "First payload fetch should miss cache"

    p2 = RouteScoringEngine.get_route_scoring_payload({})
    assert p2.cached is True, "Second payload fetch should hit cache"

    assert len(p1.route_scores) == len(p2.route_scores), "Payload route scores count must match"
    print("✓ Caching validated.")


def test_filtered_analytics():
    """Validate filter subsetting reduces metrics correctly."""
    print("\n--- TESTING FILTERED SUBSETTING ---")
    RouteScoringEngine.clear_cache()

    full = RouteScoringEngine.get_route_scoring_payload({})

    RouteScoringEngine.clear_cache()
    filtered = RouteScoringEngine.get_route_scoring_payload({"partner": "Swift Logico"})

    assert len(filtered.route_scores) <= len(full.route_scores), "Filtered scores count must be smaller or equal"
    print(f"Full routes scored: {len(full.route_scores)}")
    print(f"Filtered routes scored: {len(filtered.route_scores)}")
    print("✓ Filter subsetting validated.")


if __name__ == "__main__":
    print("Initializing Route Cost & Scoring Engine verification suite...")
    setup()

    test_individual_normalization()
    test_composite_calculations()
    test_rankings()
    test_comparisons_and_insights()
    test_cache()
    test_filtered_analytics()

    print("\n" + "=" * 60)
    print("All Route Cost & Scoring Engine tests passed successfully!")
    print("=" * 60)
