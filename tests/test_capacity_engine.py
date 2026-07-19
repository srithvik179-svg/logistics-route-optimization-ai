"""Verification test suite for the Network Capacity Analytics Engine (Phase 14).

Tests overview capacity metrics, node-level capacity analytics, regional breakdowns,
rankings, bottleneck detection rules, time-series trends, caching, and filtering.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.services.repository import repository
from backend.services.capacity_engine import CapacityEngine


def setup():
    """Initialize repository for tests."""
    if not repository.is_initialized():
        repository.initialize()
    CapacityEngine.clear_cache()


def test_overview_metrics():
    """Validate capacity overview metrics."""
    print("\n--- TESTING CAPACITY OVERVIEW METRICS ---")
    payload = CapacityEngine.get_capacity_analytics({})
    ov = payload.overview

    assert ov.overall_network_capacity > 0, "Overall capacity must be positive"
    assert ov.avg_hub_capacity > 0, "Avg hub capacity must be positive"
    assert ov.avg_repair_center_capacity > 0, "Avg RC capacity must be positive"
    assert ov.available_capacity > 0, "Available capacity must be positive"
    assert ov.used_capacity > 0, "Used capacity must be positive"
    assert 0.0 <= ov.capacity_utilization_pct <= 100.0, "Utilization % must be in 0-100% range"
    assert 0.0 <= ov.capacity_availability <= 100.0, "Availability % must be in 0-100% range"
    assert abs(ov.capacity_utilization_pct + ov.capacity_availability - 100.0) < 1.0, "Sum of utilization and availability must be ~100%"

    print(f"Overall Capacity: {ov.overall_network_capacity} units")
    print(f"Used Capacity: {ov.used_capacity} units")
    print(f"Available Capacity: {ov.available_capacity} units")
    print(f"Capacity Utilization Rate: {ov.capacity_utilization_pct}%")
    print(f"Capacity Availability Rate: {ov.capacity_availability}%")
    print("✓ Overview metrics validated.")


def test_node_analysis():
    """Validate hub and repair center capacity analysis details."""
    print("\n--- TESTING NODE-LEVEL CAPACITY ANALYSIS ---")
    payload = CapacityEngine.get_capacity_analytics({})
    hubs = payload.hubs_analysis
    rcs = payload.repair_centers_analysis

    assert len(hubs) > 0, "Hubs analysis list must not be empty"
    assert len(rcs) > 0, "RCs analysis list must not be empty"

    # Hub verification
    first_hub = hubs[0]
    assert len(first_hub.node_id) > 0, "Node ID must not be empty"
    assert first_hub.capacity > 0, "Node capacity must be positive"
    assert first_hub.used_capacity >= 0, "Used capacity must be non-negative"
    assert first_hub.utilization_pct == round((first_hub.used_capacity / first_hub.capacity) * 100.0, 1), "Utilization calculation mismatch"
    assert first_hub.remaining_capacity == round(first_hub.capacity - first_hub.used_capacity, 2), "Remaining capacity mismatch"
    assert first_hub.workload >= 0, "Workload must be non-negative"
    assert first_hub.throughput >= 0, "Throughput must be non-negative"
    assert first_hub.shipment_density >= 0, "Shipment density must be non-negative"
    assert first_hub.inventory_density >= 0, "Inventory density must be non-negative"

    print(f"Hubs analyzed count: {len(hubs)}")
    print(f"RCs analyzed count: {len(rcs)}")
    print(f"First Hub Metrics: {first_hub.model_dump()}")
    print("✓ Node-level analysis validated.")


def test_regional_analysis():
    """Validate regional, city, flow type, and partner breakdowns."""
    print("\n--- TESTING REGIONAL BREAKDOWNS ---")
    payload = CapacityEngine.get_capacity_analytics({})
    reg = payload.regional_analysis

    assert len(reg.by_region) > 0, "by_region breakdown must not be empty"
    assert len(reg.by_city) > 0, "by_city breakdown must not be empty"
    assert len(reg.by_hub_type) > 0, "by_hub_type breakdown must not be empty"
    assert len(reg.by_flow_type) > 0, "by_flow_type breakdown must not be empty"
    assert len(reg.by_logistics_partner) > 0, "by_logistics_partner breakdown must not be empty"

    # Verify a breakdown item structure
    first_region = list(reg.by_region.keys())[0]
    dim = reg.by_region[first_region]
    assert dim.capacity > 0, "Region capacity must be positive"
    assert dim.used >= 0, "Region used capacity must be non-negative"
    assert dim.utilization_pct == round((dim.used / dim.capacity) * 100.0, 1), "Region utilization mismatch"

    print(f"Regions found: {list(reg.by_region.keys())}")
    print(f"Cities found: {list(reg.by_city.keys())}")
    print(f"Hub Types: {list(reg.by_hub_type.keys())}")
    print("✓ Multi-dimensional breakdowns validated.")


def test_bottlenecks():
    """Validate bottleneck and saturation rules detection."""
    print("\n--- TESTING BOTTLENECK DETECTION ---")
    payload = CapacityEngine.get_capacity_analytics({})
    bt = payload.bottlenecks

    assert isinstance(bt.overloaded_hubs, list), "overloaded_hubs must be a list"
    assert isinstance(bt.underutilized_hubs, list), "underutilized_hubs must be a list"
    assert isinstance(bt.overloaded_repair_centers, list), "overloaded_repair_centers must be a list"
    assert isinstance(bt.idle_repair_centers, list), "idle_repair_centers must be a list"
    assert isinstance(bt.capacity_saturation_flag, bool), "capacity_saturation_flag must be a boolean"
    assert isinstance(bt.capacity_imbalance_flag, bool), "capacity_imbalance_flag must be a boolean"
    assert bt.total_bottlenecks >= 0, "Total bottlenecks count must be non-negative"

    # Verify bottleneck anomaly fields
    for anomaly in bt.underutilized_hubs[:1]:
        assert len(anomaly.entity_id) > 0, "Entity ID must not be empty"
        assert anomaly.utilization_pct >= 0, "Utilization must be non-negative"
        assert len(anomaly.description) > 0, "Description must not be empty"

    print(f"Overloaded Hubs: {len(bt.overloaded_hubs)}")
    print(f"Underutilized Hubs: {len(bt.underutilized_hubs)}")
    print(f"Overloaded RCs: {len(bt.overloaded_repair_centers)}")
    print(f"Idle RCs: {len(bt.idle_repair_centers)}")
    print(f"Capacity Saturation Flag: {bt.capacity_saturation_flag}")
    print(f"Capacity Imbalance Flag: {bt.capacity_imbalance_flag}")
    print("✓ Bottleneck detection validated.")


def test_rankings():
    """Validate capacity rankings ordering."""
    print("\n--- TESTING CAPACITY RANKINGS ---")
    payload = CapacityEngine.get_capacity_analytics({})
    rk = payload.rankings

    assert len(rk.top_utilized_hubs) > 0, "Top hubs rankings must not be empty"
    assert len(rk.least_utilized_hubs) > 0, "Least hubs rankings must not be empty"
    assert len(rk.top_utilized_repair_centers) > 0, "Top RCs rankings must not be empty"
    assert len(rk.least_utilized_repair_centers) > 0, "Least RCs rankings must not be empty"
    assert len(rk.highest_capacity_regions) > 0, "Highest capacity regions must not be empty"
    assert len(rk.lowest_capacity_regions) > 0, "Lowest capacity regions must not be empty"

    # Sorting verification
    for i in range(len(rk.top_utilized_hubs) - 1):
        assert rk.top_utilized_hubs[i].metric_value >= rk.top_utilized_hubs[i+1].metric_value, "Top hubs must be sorted descending"
    for i in range(len(rk.least_utilized_hubs) - 1):
        assert rk.least_utilized_hubs[i].metric_value <= rk.least_utilized_hubs[i+1].metric_value, "Least hubs must be sorted ascending"

    print(f"Top Utilized Hubs: {[n.entity_name for n in rk.top_utilized_hubs]}")
    print(f"Least Utilized Hubs: {[n.entity_name for n in rk.least_utilized_hubs]}")
    print("✓ Rankings validated.")


def test_trends():
    """Validate daily/weekly/monthly/quarterly trends."""
    print("\n--- TESTING CAPACITY TRENDS ---")
    payload = CapacityEngine.get_capacity_analytics({})
    tr = payload.trends

    assert len(tr.daily) > 0, "Daily trends must not be empty"
    assert len(tr.weekly) > 0, "Weekly trends must not be empty"
    assert len(tr.monthly) > 0, "Monthly trends must not be empty"
    assert len(tr.quarterly) > 0, "Quarterly trends must not be empty"

    first_daily = tr.daily[0]
    assert first_daily.total_capacity > 0, "Total capacity must be positive"
    assert first_daily.used_capacity >= 0, "Used capacity must be non-negative"
    assert 0.0 <= first_daily.availability_rate <= 100.0, "Availability rate must be in 0-100% bounds"

    print(f"Daily points count: {len(tr.daily)}")
    print(f"Weekly points count: {len(tr.weekly)}")
    print(f"Monthly points count: {len(tr.monthly)}")
    print(f"Quarterly points count: {len(tr.quarterly)}")
    print("✓ Trends validated.")


def test_cache():
    """Validate cache hits return payload with cached=True flag."""
    print("\n--- TESTING CACHE MECHANICS ---")
    CapacityEngine.clear_cache()

    p1 = CapacityEngine.get_capacity_analytics({})
    assert p1.cached is False, "First payload fetch should miss cache"

    p2 = CapacityEngine.get_capacity_analytics({})
    assert p2.cached is True, "Second payload fetch should hit cache"

    assert p1.overview.overall_network_capacity == p2.overview.overall_network_capacity, "Payload totals must match"
    print("✓ Caching validated.")


def test_filtered_analytics():
    """Validate filter subsetting reduces metrics correctly."""
    print("\n--- TESTING FILTERED SUBSETTING ---")
    CapacityEngine.clear_cache()

    full = CapacityEngine.get_capacity_analytics({})

    CapacityEngine.clear_cache()
    filtered = CapacityEngine.get_capacity_analytics({"partner": "Swift LogiCo"})

    # Since filtered transactions are fewer, the workload/throughput on nodes must be smaller or equal
    full_workload = sum(n.workload for n in full.hubs_analysis)
    filt_workload = sum(n.workload for n in filtered.hubs_analysis)

    assert filt_workload <= full_workload, "Filtered workload must be smaller or equal"

    print(f"Unfiltered workload sum: {full_workload}")
    print(f"Filtered workload sum: {filt_workload}")
    print("✓ Filter subsetting validated.")


if __name__ == "__main__":
    print("Initializing Network Capacity Analytics Engine verification suite...")
    setup()

    test_overview_metrics()
    test_node_analysis()
    test_regional_analysis()
    test_bottlenecks()
    test_rankings()
    test_trends()
    test_cache()
    test_filtered_analytics()

    print("\n" + "=" * 60)
    print("All Network Capacity Analytics Engine tests passed successfully!")
    print("=" * 60)
