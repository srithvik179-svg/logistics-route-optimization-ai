"""Verification test suite for the SLA Analytics Engine (Phase 15).

Tests overview SLA compliance metrics, dimensional breakdowns, violation analysis,
rankings, time-series trends, caching, and filtering.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.services.repository import repository
from backend.services.sla_engine import SLAEngine


def setup():
    """Initialize repository for tests."""
    if not repository.is_initialized():
        repository.initialize()
    SLAEngine.clear_cache()


def test_overview_metrics():
    """Validate SLA overview metrics."""
    print("\n--- TESTING SLA OVERVIEW METRICS ---")
    payload = SLAEngine.get_sla_payload({})
    ov = payload.overview

    assert ov.total_shipments > 0, "Total shipments must be positive"
    assert 0.0 <= ov.overall_compliance_pct <= 100.0, "Compliance must be in 0-100% bounds"
    assert ov.sla_met_count >= 0, "SLA met count must be non-negative"
    assert ov.sla_violations >= 0, "SLA violations count must be non-negative"
    assert ov.sla_met_count + ov.sla_violations == ov.total_shipments, "Met + violations must equal total"
    assert ov.avg_delay_beyond_sla >= 0, "Avg delay beyond SLA must be non-negative"
    assert ov.avg_early_completion >= 0, "Avg early completion must be non-negative"
    assert ov.sla_success_rate == ov.overall_compliance_pct, "Success rate must equal compliance %"

    print(f"Overall Compliance Rate: {ov.overall_compliance_pct}%")
    print(f"Total evaluated shipments: {ov.total_shipments}")
    print(f"SLA Met count: {ov.sla_met_count}, Violations count: {ov.sla_violations}")
    print(f"Avg delay: {ov.avg_delay_beyond_sla} days, Avg early completion: {ov.avg_early_completion} days")
    print("✓ Overview metrics validated.")


def test_breakdowns():
    """Validate SLA breakdowns across all dimensions."""
    print("\n--- TESTING SLA BREAKDOWNS ---")
    payload = SLAEngine.get_sla_payload({})
    bd = payload.breakdowns

    assert len(bd.by_hub) > 0, "by_hub breakdown must not be empty"
    assert len(bd.by_repair_center) > 0, "by_repair_center breakdown must not be empty"
    assert len(bd.by_partner) > 0, "by_partner breakdown must not be empty"
    assert len(bd.by_route) > 0, "by_route breakdown must not be empty"
    assert len(bd.by_region) > 0, "by_region breakdown must not be empty"
    assert len(bd.by_priority) > 0, "by_priority breakdown must not be empty"
    assert len(bd.by_category) > 0, "by_category breakdown must not be empty"

    # Verify a breakdown item structure
    first_hub = bd.by_hub[0]
    assert len(first_hub.name) > 0, "Entity name must not be empty"
    assert 0.0 <= first_hub.compliance_pct <= 100.0, "Compliance rate must be in 0-100% bounds"
    assert first_hub.total_count >= 0, "Total count must be non-negative"
    assert first_hub.violations >= 0, "Violations must be non-negative"
    assert first_hub.violations <= first_hub.total_count, "Violations count must be <= total count"

    print(f"Hubs breakdown size: {len(bd.by_hub)}")
    print(f"Partners breakdown size: {len(bd.by_partner)}")
    print(f"Routes breakdown size: {len(bd.by_route)}")
    print("✓ Dimensional breakdowns validated.")


def test_violations():
    """Validate repeated violations and critical delay analyses."""
    print("\n--- TESTING VIOLATION ANALYSIS ---")
    payload = SLAEngine.get_sla_payload({})
    vi = payload.violations_analysis

    assert vi.total_violations_recorded >= 0, "Total violations must be non-negative"
    assert isinstance(vi.high_delay_routes, list), "high_delay_routes must be a list"
    assert isinstance(vi.repeated_sla_violations, list), "repeated_sla_violations must be a list"
    assert isinstance(vi.critical_delay_locations, list), "critical_delay_locations must be a list"
    assert isinstance(vi.critical_logistics_partners, list), "critical_logistics_partners must be a list"
    assert isinstance(vi.frequently_delayed_parts, list), "frequently_delayed_parts must be a list"

    # Verify violation entity structure
    for entity in vi.high_delay_routes[:1]:
        assert len(entity.name) > 0, "Entity name must not be empty"
        assert entity.violation_count > 0, "Violation count must be positive"
        assert entity.avg_delay_days > 0, "Avg delay must be positive"
        assert entity.risk_level in ["Critical", "High", "Medium", "Low"], "Invalid risk classification"

    print(f"Total violations recorded: {vi.total_violations_recorded}")
    print(f"High delay routes count: {len(vi.high_delay_routes)}")
    print(f"Repeated violations count: {len(vi.repeated_sla_violations)}")
    print(f"Critical delay locations count: {len(vi.critical_delay_locations)}")
    print(f"Frequently delayed parts count: {len(vi.frequently_delayed_parts)}")
    print("✓ Violations analysis validated.")


def test_rankings():
    """Validate reliability rankings sorting."""
    print("\n--- TESTING RELIABILITY RANKINGS ---")
    payload = SLAEngine.get_sla_payload({})
    rk = payload.rankings

    assert len(rk.best_performing_hubs) > 0, "Best performing hubs rankings must not be empty"
    assert len(rk.worst_performing_hubs) > 0, "Worst performing hubs rankings must not be empty"
    assert len(rk.best_logistics_partners) > 0, "Best partners rankings must not be empty"
    assert len(rk.worst_logistics_partners) > 0, "Worst partners rankings must not be empty"
    assert len(rk.best_repair_centers) > 0, "Best RCs rankings must not be empty"
    assert len(rk.worst_repair_centers) > 0, "Worst RCs rankings must not be empty"
    assert len(rk.most_reliable_routes) > 0, "Most reliable routes rankings must not be empty"
    assert len(rk.least_reliable_routes) > 0, "Least reliable routes rankings must not be empty"

    # Verify sorting
    for i in range(len(rk.best_performing_hubs) - 1):
        assert rk.best_performing_hubs[i].compliance_pct >= rk.best_performing_hubs[i+1].compliance_pct, "Best hubs must be sorted descending"
    for i in range(len(rk.worst_performing_hubs) - 1):
        assert rk.worst_performing_hubs[i].compliance_pct <= rk.worst_performing_hubs[i+1].compliance_pct, "Worst hubs must be sorted ascending"

    print(f"Best Hubs: {[h.entity_name for h in rk.best_performing_hubs]}")
    print(f"Worst Hubs: {[h.entity_name for h in rk.worst_performing_hubs]}")
    print("✓ Reliability rankings validated.")


def test_trends():
    """Validate daily/weekly/monthly/quarterly trends."""
    print("\n--- TESTING SLA TRENDS ---")
    payload = SLAEngine.get_sla_payload({})
    tr = payload.trends

    assert len(tr.daily) > 0, "Daily trends must not be empty"
    assert len(tr.weekly) > 0, "Weekly trends must not be empty"
    assert len(tr.monthly) > 0, "Monthly trends must not be empty"
    assert len(tr.quarterly) > 0, "Quarterly trends must not be empty"

    first_daily = tr.daily[0]
    assert 0.0 <= first_daily.compliance_pct <= 100.0, "Compliance must be in 0-100% range"
    assert first_daily.total_shipments > 0, "Total shipments must be positive"
    assert first_daily.violation_count >= 0, "Violations must be non-negative"

    print(f"Daily points count: {len(tr.daily)}")
    print(f"Weekly points count: {len(tr.weekly)}")
    print(f"Monthly points count: {len(tr.monthly)}")
    print(f"Quarterly points count: {len(tr.quarterly)}")
    print("✓ SLA trend datasets validated.")


def test_cache():
    """Validate cache hits return payload with cached=True flag."""
    print("\n--- TESTING CACHE MECHANICS ---")
    SLAEngine.clear_cache()

    p1 = SLAEngine.get_sla_payload({})
    assert p1.cached is False, "First payload fetch should miss cache"

    p2 = SLAEngine.get_sla_payload({})
    assert p2.cached is True, "Second payload fetch should hit cache"

    assert p1.overview.overall_compliance_pct == p2.overview.overall_compliance_pct, "Payload totals must match"
    print("✓ Caching validated.")


def test_filtered_analytics():
    """Validate filter subsetting reduces metrics correctly."""
    print("\n--- TESTING FILTERED SUBSETTING ---")
    SLAEngine.clear_cache()

    full = SLAEngine.get_sla_payload({})

    SLAEngine.clear_cache()
    filtered = SLAEngine.get_sla_payload({"partner": "Swift LogiCo"})

    assert filtered.overview.total_shipments <= full.overview.total_shipments, \
        "Filtered shipments count must be smaller or equal to full count"

    print(f"Unfiltered shipments count: {full.overview.total_shipments}")
    print(f"Filtered shipments count: {filtered.overview.total_shipments}")
    print("✓ Filter subsetting validated.")


if __name__ == "__main__":
    print("Initializing SLA Analytics Engine verification suite...")
    setup()

    test_overview_metrics()
    test_breakdowns()
    test_violations()
    test_rankings()
    test_trends()
    test_cache()
    test_filtered_analytics()

    print("\n" + "=" * 60)
    print("All SLA Analytics Engine tests passed successfully!")
    print("=" * 60)
