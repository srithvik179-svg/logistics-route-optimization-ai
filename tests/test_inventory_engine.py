"""Verification test suite for the Logistics Inventory Analytics Engine (Phase 13).

Tests overview metrics, movement breakdowns, stock level classifications, node capacity
utilization, rankings, outlier anomaly detection, trends, and caching.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.services.repository import repository
from backend.services.inventory_engine import InventoryEngine


def setup():
    """Initialize repository for tests."""
    if not repository.is_initialized():
        repository.initialize()
    InventoryEngine.clear_cache()


def test_overview_metrics():
    """Validate 11 overview inventory KPIs."""
    print("\n--- TESTING INVENTORY OVERVIEW METRICS ---")
    payload = InventoryEngine.get_inventory_payload({})
    ov = payload.overview

    assert ov.total_inventory > 0, "Total inventory must be positive"
    assert ov.avg_inventory > 0, "Avg inventory must be positive"
    assert ov.min_inventory >= 0, "Min inventory must be non-negative"
    assert ov.max_inventory >= ov.min_inventory, "Max must be >= min"
    assert ov.inventory_variance >= 0, "Variance must be non-negative"
    assert ov.inventory_std_deviation >= 0, "Std dev must be non-negative"
    
    assert len(ov.inventory_per_hub) > 0, "Per-hub inventory map must not be empty"
    assert len(ov.inventory_per_repair_center) > 0, "Per-RC inventory map must not be empty"
    assert len(ov.inventory_per_part_category) > 0, "Per-category inventory map must not be empty"
    assert len(ov.inventory_per_region) > 0, "Per-region inventory map must not be empty"
    assert len(ov.inventory_per_partner) > 0, "Per-partner inventory map must not be empty"

    print(f"Total Network Inventory: {ov.total_inventory} units")
    print(f"Avg Inventory: {ov.avg_inventory} units")
    print(f"Min: {ov.min_inventory}, Max: {ov.max_inventory}")
    print(f"Std Dev: {ov.inventory_std_deviation}, Variance: {ov.inventory_variance}")
    print(f"Inventory per Hubs: {ov.inventory_per_hub}")
    print(f"Inventory per RCs: {ov.inventory_per_repair_center}")
    print("✓ Overview metrics validated.")


def test_movement():
    """Validate inventory incoming, outgoing and net movement breakdowns."""
    print("\n--- TESTING INVENTORY MOVEMENT BREAKDOWNS ---")
    payload = InventoryEngine.get_inventory_payload({})
    mov = payload.movement

    assert mov.incoming_total > 0, "Incoming total must be positive"
    assert mov.outgoing_total > 0, "Outgoing total must be positive"
    
    assert len(mov.by_hub) > 0, "Movement by Hub must not be empty"
    assert len(mov.by_region) > 0, "Movement by Region must not be empty"
    assert len(mov.by_part) > 0, "Movement by Part must not be empty"
    assert len(mov.by_month) > 0, "Movement by Month must not be empty"
    assert len(mov.by_quarter) > 0, "Movement by Quarter must not be empty"

    # Verify structure of one hub movement
    first_hub = list(mov.by_hub.keys())[0]
    dim = mov.by_hub[first_hub]
    assert dim.incoming >= 0, "Incoming must be non-negative"
    assert dim.outgoing >= 0, "Outgoing must be non-negative"
    assert dim.net_movement == round(dim.incoming - dim.outgoing, 2), "Net movement calculation mismatch"

    print(f"Total incoming flow: {mov.incoming_total} units")
    print(f"Hub movements: {list(mov.by_hub.keys())}")
    print(f"Region movements: {list(mov.by_region.keys())}")
    print("✓ Inventory movement validated.")


def test_stock_analysis():
    """Validate stock levels classification."""
    print("\n--- TESTING STOCK LEVELS CLASSIFICATION ---")
    payload = InventoryEngine.get_inventory_payload({})
    sa = payload.stock_analysis

    assert isinstance(sa.high_stock_items, list), "high_stock_items must be a list"
    assert isinstance(sa.low_stock_items, list), "low_stock_items must be a list"
    assert isinstance(sa.critical_stock_items, list), "critical_stock_items must be a list"
    assert isinstance(sa.zero_stock_items, list), "zero_stock_items must be a list"
    assert len(sa.fast_moving_parts) > 0, "Fast moving parts list must not be empty"
    assert len(sa.slow_moving_parts) > 0, "Slow moving parts list must not be empty"

    print(f"High Stock count: {len(sa.high_stock_items)}")
    print(f"Low Stock count: {len(sa.low_stock_items)}")
    print(f"Critical Stock count: {len(sa.critical_stock_items)}")
    print(f"Zero Stock count: {len(sa.zero_stock_items)}")
    print(f"Fast Moving Parts: {sa.fast_moving_parts}")
    print(f"Slow Moving Parts: {sa.slow_moving_parts}")
    print("✓ Stock analysis validated.")


def test_utilization():
    """Validate node capacity utilization and turnover ratios."""
    print("\n--- TESTING CAPACITY UTILIZATION ---")
    payload = InventoryEngine.get_inventory_payload({})
    ut = payload.utilization

    assert len(ut.hub_utilization) > 0, "Hub utilization list must not be empty"
    assert len(ut.repair_center_utilization) > 0, "RC utilization list must not be empty"
    assert ut.avg_inventory_capacity > 0, "Average capacity must be positive"
    assert 0.0 <= ut.inventory_occupancy <= 100.0, "Occupancy must be in 0-100% bounds"
    assert ut.inventory_turnover_ratio >= 0, "Turnover ratio must be non-negative"

    print(f"Hub occupancy rates: {ut.hub_utilization}")
    print(f"RC occupancy rates: {ut.repair_center_utilization}")
    print(f"Average capacity: {ut.avg_inventory_capacity} units")
    print(f"Network Occupancy: {ut.inventory_occupancy}%")
    print(f"Network Turnover Ratio: {ut.inventory_turnover_ratio}")
    print("✓ Utilization analysis validated.")


def test_rankings():
    """Validate inventory rankings."""
    print("\n--- TESTING INVENTORY RANKINGS ---")
    payload = InventoryEngine.get_inventory_payload({})
    rk = payload.rankings

    assert len(rk.top_inventory_hubs) > 0, "Top inventory hubs must not be empty"
    assert len(rk.lowest_inventory_hubs) > 0, "Lowest inventory hubs must not be empty"
    assert len(rk.top_repair_centers) > 0, "Top repair centers must not be empty"
    assert len(rk.top_moving_parts) > 0, "Top moving parts must not be empty"
    assert len(rk.slowest_moving_parts) > 0, "Slowest moving parts must not be empty"

    # Verify ranks ordering
    for i in range(len(rk.top_inventory_hubs) - 1):
        assert rk.top_inventory_hubs[i].value >= rk.top_inventory_hubs[i+1].value, "Top hubs must be sorted descending"
    for i in range(len(rk.lowest_inventory_hubs) - 1):
        assert rk.lowest_inventory_hubs[i].value <= rk.lowest_inventory_hubs[i+1].value, "Lowest hubs must be sorted ascending"

    print(f"Top Stock Hubs: {[h.name for h in rk.top_inventory_hubs]}")
    print(f"Top Moving Parts: {[p.name for p in rk.top_moving_parts]}")
    print("✓ Rankings validated.")


def test_outliers():
    """Validate outlier anomalies detection."""
    print("\n--- TESTING OUTLIER DETECTION ---")
    payload = InventoryEngine.get_inventory_payload({})
    out = payload.outliers

    assert out.total_anomalies >= 0, "Total anomalies must be non-negative"
    assert isinstance(out.spikes, list), "Spikes must be a list"
    assert isinstance(out.drops, list), "Drops must be a list"
    assert isinstance(out.abnormal_levels, list), "Abnormal levels must be a list"
    assert isinstance(out.potential_overstock, list), "Potential overstock must be a list"
    assert isinstance(out.potential_understock, list), "Potential understock must be a list"

    print(f"Spikes: {len(out.spikes)}")
    print(f"Drops: {len(out.drops)}")
    print(f"Abnormal levels: {len(out.abnormal_levels)}")
    print(f"Potential Overstock: {len(out.potential_overstock)}")
    print(f"Potential Understock: {len(out.potential_understock)}")
    print(f"Total Unique Anomalies: {out.total_anomalies}")
    print("✓ Outlier detection validated.")


def test_trends():
    """Validate daily/weekly/monthly/quarterly trends."""
    print("\n--- TESTING TRENDS ---")
    payload = InventoryEngine.get_inventory_payload({})
    tr = payload.trends

    assert len(tr.daily) > 0, "Daily trends must not be empty"
    assert len(tr.weekly) > 0, "Weekly trends must not be empty"
    assert len(tr.monthly) > 0, "Monthly trends must not be empty"
    assert len(tr.quarterly) > 0, "Quarterly trends must not be empty"

    first_daily = tr.daily[0]
    assert first_daily.avg_stock_level > 0, "Daily stock level must be positive"
    assert first_daily.incoming_units >= 0, "Incoming units must be non-negative"
    assert len(first_daily.period) > 0, "Period label must not be empty"

    print(f"Daily points count: {len(tr.daily)}")
    print(f"Weekly points count: {len(tr.weekly)}")
    print(f"Monthly points count: {len(tr.monthly)}")
    print(f"Quarterly points count: {len(tr.quarterly)}")
    print("✓ Trend datasets validated.")


def test_cache():
    """Validate cache hits return payload with cached=True flag."""
    print("\n--- TESTING CACHE MECHANICS ---")
    InventoryEngine.clear_cache()

    p1 = InventoryEngine.get_inventory_payload({})
    assert p1.cached is False, "First payload fetch should miss cache"

    p2 = InventoryEngine.get_inventory_payload({})
    assert p2.cached is True, "Second payload fetch should hit cache"
    
    assert p1.overview.total_inventory == p2.overview.total_inventory, "Payload totals must match"
    print("✓ Caching validated.")


def test_filtered_analytics():
    """Validate filter subsetting reduces metrics correctly."""
    print("\n--- TESTING FILTERED SUBSETTING ---")
    InventoryEngine.clear_cache()
    
    full = InventoryEngine.get_inventory_payload({})
    
    InventoryEngine.clear_cache()
    filtered = InventoryEngine.get_inventory_payload({"partner": "Swift LogiCo"})
    
    assert filtered.movement.incoming_total <= full.movement.incoming_total, \
        "Filtered movement must be smaller or equal to full movement"
    
    print(f"Unfiltered incoming units: {full.movement.incoming_total}")
    print(f"Filtered incoming units: {filtered.movement.incoming_total}")
    print("✓ Filter subsetting validated.")


if __name__ == "__main__":
    print("Initializing Logistics Inventory Analytics Engine verification suite...")
    setup()

    test_overview_metrics()
    test_movement()
    test_stock_analysis()
    test_utilization()
    test_rankings()
    test_outliers()
    test_trends()
    test_cache()
    test_filtered_analytics()

    print("\n" + "=" * 60)
    print("All Logistics Inventory Analytics Engine tests passed successfully!")
    print("=" * 60)
