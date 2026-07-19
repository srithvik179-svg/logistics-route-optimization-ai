"""Verification test suite for the Transit Time Analytics Engine (Phase 12).

Tests overview metrics, distribution, rankings, trends, outliers, and caching.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.services.repository import repository
from backend.services.transit_engine import TransitEngine


def setup():
    """Initialize repository for tests."""
    if not repository.is_initialized():
        repository.initialize()
    TransitEngine.clear_cache()


def test_overview_metrics():
    """Validate 13 overview transit KPIs."""
    print("\n--- TESTING TRANSIT OVERVIEW METRICS ---")
    payload = TransitEngine.get_transit_analytics({})
    ov = payload.overview

    assert ov.total_shipments > 0, "Total shipments must be positive"
    assert ov.avg_transit_time >= 0, "Avg transit time must be non-negative"
    assert ov.median_transit_time >= 0, "Median must be non-negative"
    assert ov.max_transit_time >= ov.min_transit_time, "Max must be >= min"
    assert ov.max_transit_time >= ov.median_transit_time, "Max must be >= median"
    assert ov.transit_variance >= 0, "Variance must be non-negative"
    assert ov.transit_std_deviation >= 0, "Std dev must be non-negative"
    assert ov.avg_transit_per_route >= 0, "Per-route avg must be non-negative"
    assert ov.avg_transit_per_hub >= 0, "Per-hub avg must be non-negative"
    assert ov.avg_transit_per_repair_center >= 0, "Per-RC avg must be non-negative"
    assert ov.avg_transit_per_partner >= 0, "Per-partner avg must be non-negative"
    assert ov.avg_transit_per_priority >= 0, "Per-priority avg must be non-negative"
    assert ov.avg_transit_per_flow_type >= 0, "Per-flow-type avg must be non-negative"

    print(f"Avg Transit: {ov.avg_transit_time} days")
    print(f"Median Transit: {ov.median_transit_time} days")
    print(f"Min: {ov.min_transit_time}, Max: {ov.max_transit_time}")
    print(f"Std Dev: {ov.transit_std_deviation}, Variance: {ov.transit_variance}")
    print(f"Total Shipments: {ov.total_shipments}")
    print("✓ Overview metrics validated.")


def test_distribution():
    """Validate transit distribution analysis."""
    print("\n--- TESTING TRANSIT DISTRIBUTION ---")
    payload = TransitEngine.get_transit_analytics({})
    dist = payload.distribution

    assert len(dist.histogram) > 0, "Histogram must not be empty"
    assert len(dist.categories) == 4, "Must have 4 categories (Fast/Normal/Slow/Critical Delay)"
    assert len(dist.frequency) > 0, "Frequency map must not be empty"

    # Category names
    cat_names = [c.category for c in dist.categories]
    assert "Fast" in cat_names, "Must include Fast category"
    assert "Normal" in cat_names, "Must include Normal category"
    assert "Slow" in cat_names, "Must include Slow category"
    assert "Critical Delay" in cat_names, "Must include Critical Delay category"

    # Total percentage should sum to ~100
    total_pct = sum(c.percentage for c in dist.categories)
    assert 99.0 <= total_pct <= 101.0, f"Category percentages must sum to ~100, got {total_pct}"

    # Histogram bucket structure
    first_bucket = dist.histogram[0]
    assert first_bucket.count >= 0, "Bucket count must be non-negative"
    assert first_bucket.percentage >= 0, "Bucket percentage must be non-negative"

    print(f"Histogram: {len(dist.histogram)} buckets")
    print(f"Categories: {[(c.category, c.count, f'{c.percentage}%') for c in dist.categories]}")
    print(f"Frequency map keys: {sorted(dist.frequency.keys())}")
    print("✓ Distribution validated.")


def test_rankings():
    """Validate all 8 ranking lists."""
    print("\n--- TESTING TRANSIT RANKINGS ---")
    payload = TransitEngine.get_transit_analytics({})
    rk = payload.rankings

    # Fastest routes should be sorted ascending
    if len(rk.fastest_routes) > 1:
        for i in range(len(rk.fastest_routes) - 1):
            assert rk.fastest_routes[i].avg_transit_time <= rk.fastest_routes[i + 1].avg_transit_time, \
                "Fastest routes must be sorted ascending"

    # Slowest routes should be sorted descending
    if len(rk.slowest_routes) > 1:
        for i in range(len(rk.slowest_routes) - 1):
            assert rk.slowest_routes[i].avg_transit_time >= rk.slowest_routes[i + 1].avg_transit_time, \
                "Slowest routes must be sorted descending"

    # Ranks should be 1-indexed
    for entry in rk.fastest_routes:
        assert entry.rank >= 1, "Rank must be 1-indexed"
        assert entry.shipment_count > 0, "Shipment count must be positive"

    print(f"Fastest Routes: {len(rk.fastest_routes)}, Slowest Routes: {len(rk.slowest_routes)}")
    print(f"Fastest Hubs: {len(rk.fastest_hubs)}, Slowest Hubs: {len(rk.slowest_hubs)}")
    print(f"Fastest RCs: {len(rk.fastest_repair_centers)}, Slowest RCs: {len(rk.slowest_repair_centers)}")
    print(f"Fastest Partners: {len(rk.fastest_partners)}, Slowest Partners: {len(rk.slowest_partners)}")
    print("✓ Rankings validated.")


def test_trends():
    """Validate all 4 transit trend granularities."""
    print("\n--- TESTING TRANSIT TRENDS ---")
    payload = TransitEngine.get_transit_analytics({})
    tr = payload.trends

    assert len(tr.daily) > 0, "Daily trends must not be empty"
    assert len(tr.monthly) > 0, "Monthly trends must not be empty"

    first = tr.daily[0]
    assert first.avg_transit_time >= 0, "Avg transit must be non-negative"
    assert first.total_shipments > 0, "Total shipments must be positive"
    assert 0 <= first.on_time_pct <= 100, "On-time pct must be 0-100"
    assert len(first.period) > 0, "Period label must not be empty"

    print(f"Daily: {len(tr.daily)}, Weekly: {len(tr.weekly)}")
    print(f"Monthly: {len(tr.monthly)}, Quarterly: {len(tr.quarterly)}")
    print("✓ Trends validated.")


def test_outliers():
    """Validate outlier detection structure."""
    print("\n--- TESTING TRANSIT OUTLIERS ---")
    payload = TransitEngine.get_transit_analytics({})
    out = payload.outliers

    # Outlier structure is valid even if counts are 0
    assert out.total_outliers >= 0, "Total outliers must be non-negative"
    assert isinstance(out.extremely_slow, list), "extremely_slow must be a list"
    assert isinstance(out.extremely_fast, list), "extremely_fast must be a list"
    assert isinstance(out.abnormal, list), "abnormal must be a list"
    assert isinstance(out.long_delay_candidates, list), "long_delay_candidates must be a list"

    # If there are outliers, validate their structure
    for outlier in out.extremely_slow[:1]:
        assert outlier.transit_days > 0, "Outlier transit days must be positive"
        assert outlier.outlier_type == "extremely_slow", "Type must match"
        assert len(outlier.transaction_id) > 0, "Transaction ID must not be empty"

    print(f"Extremely Slow: {len(out.extremely_slow)}")
    print(f"Extremely Fast: {len(out.extremely_fast)}")
    print(f"Abnormal: {len(out.abnormal)}")
    print(f"Long Delay Candidates: {len(out.long_delay_candidates)}")
    print(f"Total Unique Outliers: {out.total_outliers}")
    print("✓ Outliers validated.")


def test_cache():
    """Validate cache hit returns identical payload with cached=True."""
    print("\n--- TESTING CACHE ---")
    TransitEngine.clear_cache()

    payload1 = TransitEngine.get_transit_analytics({})
    assert payload1.cached is False, "First call should be a cache miss"

    payload2 = TransitEngine.get_transit_analytics({})
    assert payload2.cached is True, "Second call should be a cache hit"

    assert payload1.overview.avg_transit_time == payload2.overview.avg_transit_time, \
        "Cached value must match original"
    assert payload1.overview.total_shipments == payload2.overview.total_shipments, \
        "Cached total must match original"

    print("✓ Cache hit validated.")


def test_filtered_analytics():
    """Validate filtered transit analytics narrows the dataset."""
    print("\n--- TESTING FILTERED ANALYTICS ---")
    TransitEngine.clear_cache()

    full = TransitEngine.get_transit_analytics({})
    TransitEngine.clear_cache()
    filtered = TransitEngine.get_transit_analytics({"status": "MET"})

    assert filtered.overview.total_shipments <= full.overview.total_shipments, \
        "Filtered shipments must be <= unfiltered"
    assert filtered.overview.total_shipments > 0, "Filtered result should have some MET shipments"

    print(f"Unfiltered: {full.overview.total_shipments}, Filtered (MET): {filtered.overview.total_shipments}")
    print("✓ Filter subsetting validated.")


if __name__ == "__main__":
    print("Initializing Transit Time Analytics Engine verification suite...")
    setup()

    test_overview_metrics()
    test_distribution()
    test_rankings()
    test_trends()
    test_outliers()
    test_cache()
    test_filtered_analytics()

    print("\n" + "=" * 60)
    print("All Transit Time Analytics Engine tests passed successfully!")
    print("=" * 60)
