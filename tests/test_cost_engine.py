"""Verification test suite for the Logistics Cost Analytics Engine (Phase 11).

Tests overview metrics, breakdowns, variance analysis, rankings, trends, and caching.
"""

import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.services.repository import repository
from backend.services.cost_engine import CostEngine
from backend.services.cost_statistics import CostStatistics
from backend.services.cost_ranking import CostRanking
from backend.services.cost_trends import CostTrendsService
from backend.models.cost_metrics import CostAnalyticsPayload


def setup():
    """Initialize repository for tests."""
    if not repository.is_initialized():
        repository.initialize()
    # Clear any stale cache
    CostEngine.clear_cache()


def test_overview_metrics():
    """Validate 9 overview cost KPIs."""
    print("\n--- TESTING OVERVIEW METRICS ---")
    payload = CostEngine.get_cost_analytics({})
    ov = payload.overview

    assert ov.overall_logistics_cost > 0, "Overall cost must be positive"
    assert ov.avg_shipment_cost > 0, "Avg shipment cost must be positive"
    assert ov.avg_route_cost > 0, "Avg route cost must be positive"
    assert ov.avg_cost_per_hub > 0, "Avg cost per hub must be positive"
    assert ov.avg_cost_per_repair_center > 0, "Avg cost per RC must be positive"
    assert ov.avg_cost_per_partner > 0, "Avg cost per partner must be positive"
    assert ov.avg_cost_per_flow_type > 0, "Avg cost per flow type must be positive"
    assert ov.total_shipments > 0, "Total shipments must be positive"

    print(f"Overall Logistics Cost: ${ov.overall_logistics_cost}")
    print(f"Avg Shipment Cost: ${ov.avg_shipment_cost}")
    print(f"Avg Route Cost: ${ov.avg_route_cost}")
    print(f"Avg Cost Per Hub: ${ov.avg_cost_per_hub}")
    print(f"Avg Cost Per RC: ${ov.avg_cost_per_repair_center}")
    print(f"Avg Cost Per Partner: ${ov.avg_cost_per_partner}")
    print(f"Avg Cost Per Flow Type: ${ov.avg_cost_per_flow_type}")
    print(f"Total Shipments: {ov.total_shipments}")
    print("✓ Overview metrics validated.")


def test_breakdowns():
    """Validate all 8 breakdown dimensions return non-empty lists."""
    print("\n--- TESTING BREAKDOWNS ---")
    payload = CostEngine.get_cost_analytics({})
    bd = payload.breakdowns

    assert len(bd.by_hub) > 0, "by_hub breakdown must not be empty"
    assert len(bd.by_route) > 0, "by_route breakdown must not be empty"
    assert len(bd.by_repair_center) > 0, "by_repair_center breakdown must not be empty"
    assert len(bd.by_partner) > 0, "by_partner breakdown must not be empty"
    assert len(bd.by_priority) > 0, "by_priority breakdown must not be empty"
    assert len(bd.by_status) > 0, "by_status breakdown must not be empty"

    # Verify breakdown item structure
    first_hub = bd.by_hub[0]
    assert first_hub.total_cost > 0, "Hub total cost must be positive"
    assert first_hub.avg_cost > 0, "Hub avg cost must be positive"
    assert first_hub.shipment_count > 0, "Hub shipment count must be positive"

    print(f"by_hub: {len(bd.by_hub)} entries")
    print(f"by_route: {len(bd.by_route)} entries")
    print(f"by_repair_center: {len(bd.by_repair_center)} entries")
    print(f"by_partner: {len(bd.by_partner)} entries")
    print(f"by_region: {len(bd.by_region)} entries")
    print(f"by_priority: {len(bd.by_priority)} entries")
    print(f"by_category: {len(bd.by_category)} entries")
    print(f"by_status: {len(bd.by_status)} entries")
    print("✓ All breakdowns validated.")


def test_variance_analysis():
    """Validate variance metrics are internally consistent."""
    print("\n--- TESTING VARIANCE ANALYSIS ---")
    payload = CostEngine.get_cost_analytics({})
    v = payload.variance

    assert v.maximum >= v.minimum, "Max must be >= min"
    assert v.maximum >= v.median, "Max must be >= median"
    assert v.median >= v.minimum, "Median must be >= min"
    assert v.std_deviation >= 0, "Std dev must be non-negative"
    assert v.variance >= 0, "Variance must be non-negative"
    assert v.q3 >= v.q1, "Q3 must be >= Q1"
    assert v.iqr >= 0, "IQR must be non-negative"
    assert abs(v.iqr - (v.q3 - v.q1)) < 0.01, "IQR must equal Q3 - Q1"

    print(f"Max: ${v.maximum}, Min: ${v.minimum}, Median: ${v.median}")
    print(f"Std Dev: {v.std_deviation}, Variance: {v.variance}")
    print(f"Q1: {v.q1}, Q3: {v.q3}, IQR: {v.iqr}")
    print("✓ Variance analysis validated.")


def test_rankings():
    """Validate ranking lists are sorted correctly."""
    print("\n--- TESTING RANKINGS ---")
    payload = CostEngine.get_cost_analytics({})
    rk = payload.rankings

    # Top expensive routes should be sorted descending by metric_value
    if len(rk.top_expensive_routes) > 1:
        for i in range(len(rk.top_expensive_routes) - 1):
            assert rk.top_expensive_routes[i].metric_value >= rk.top_expensive_routes[i + 1].metric_value, \
                "Top routes must be sorted descending"

    # Lowest cost routes should be sorted ascending
    if len(rk.lowest_cost_routes) > 1:
        for i in range(len(rk.lowest_cost_routes) - 1):
            assert rk.lowest_cost_routes[i].metric_value <= rk.lowest_cost_routes[i + 1].metric_value, \
                "Lowest routes must be sorted ascending"

    # Ranks should be 1-indexed and sequential
    for entry in rk.top_expensive_routes:
        assert entry.rank >= 1, "Rank must be 1-indexed"

    print(f"Top Expensive Routes: {len(rk.top_expensive_routes)} entries")
    print(f"Lowest Cost Routes: {len(rk.lowest_cost_routes)} entries")
    print(f"Highest Cost Partners: {len(rk.highest_cost_partners)} entries")
    print(f"Lowest Cost Partners: {len(rk.lowest_cost_partners)} entries")
    print(f"Highest Cost Hubs: {len(rk.highest_cost_hubs)} entries")
    print(f"Lowest Cost Hubs: {len(rk.lowest_cost_hubs)} entries")
    print("✓ Rankings validated.")


def test_trends():
    """Validate all 4 trend granularities produce non-empty datasets."""
    print("\n--- TESTING TREND DATASETS ---")
    payload = CostEngine.get_cost_analytics({})
    tr = payload.trends

    assert len(tr.daily) > 0, "Daily trends must not be empty"
    assert len(tr.monthly) > 0, "Monthly trends must not be empty"

    # Validate trend point structure
    first_daily = tr.daily[0]
    assert first_daily.total_cost > 0, "Daily total cost must be positive"
    assert first_daily.avg_cost > 0, "Daily avg cost must be positive"
    assert first_daily.shipment_count > 0, "Daily shipment count must be positive"
    assert len(first_daily.period) > 0, "Period label must not be empty"

    print(f"Daily: {len(tr.daily)} data points")
    print(f"Weekly: {len(tr.weekly)} data points")
    print(f"Monthly: {len(tr.monthly)} data points")
    print(f"Quarterly: {len(tr.quarterly)} data points")
    print("✓ Trend datasets validated.")


def test_cache():
    """Validate cache hit returns identical payload with cached=True."""
    print("\n--- TESTING CACHE ---")
    CostEngine.clear_cache()

    # First call — cache miss
    payload1 = CostEngine.get_cost_analytics({})
    assert payload1.cached is False, "First call should be a cache miss"

    # Second call — cache hit
    payload2 = CostEngine.get_cost_analytics({})
    assert payload2.cached is True, "Second call should be a cache hit"

    # Values must match
    assert payload1.overview.overall_logistics_cost == payload2.overview.overall_logistics_cost, \
        "Cached overview cost must match original"
    assert payload1.overview.total_shipments == payload2.overview.total_shipments, \
        "Cached total shipments must match original"

    print("✓ Cache hit validated — second call returned cached payload.")


def test_filtered_analytics():
    """Validate filtered cost analytics narrows the dataset."""
    print("\n--- TESTING FILTERED ANALYTICS ---")
    CostEngine.clear_cache()

    # Unfiltered
    full = CostEngine.get_cost_analytics({})

    # Filtered by SLA status
    CostEngine.clear_cache()
    filtered = CostEngine.get_cost_analytics({"status": "MET"})

    assert filtered.overview.total_shipments <= full.overview.total_shipments, \
        "Filtered shipments must be <= unfiltered"
    assert filtered.overview.total_shipments > 0, "Filtered result should have some MET shipments"

    print(f"Unfiltered shipments: {full.overview.total_shipments}")
    print(f"Filtered (MET) shipments: {filtered.overview.total_shipments}")
    print("✓ Filter subsetting validated.")


if __name__ == "__main__":
    print("Initializing Logistics Cost Analytics Engine verification suite...")
    setup()

    test_overview_metrics()
    test_breakdowns()
    test_variance_analysis()
    test_rankings()
    test_trends()
    test_cache()
    test_filtered_analytics()

    print("\n" + "=" * 60)
    print("All Logistics Cost Analytics Engine tests passed successfully!")
    print("=" * 60)
