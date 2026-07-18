import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.services.repository import repository
from backend.services.performance_service import PerformanceService

def test_performance_suite():
    print("Initializing Logistics Performance Monitoring verification suite...")
    
    # Initialize repository
    repository.initialize()
    
    # 1. Fetch default performance payload (no filters)
    print("\n--- TESTING PERFORMANCE PAYLOAD (NO FILTERS) ---")
    payload = PerformanceService.get_performance_payload({})
    
    assert "kpis" in payload
    assert "hub_scorecard" in payload
    assert "rc_scorecard" in payload
    assert "delay_analysis" in payload
    assert "cost_analysis" in payload
    assert "trends" in payload
    
    # Check KPIs
    kpis = payload["kpis"]
    print(f"Logistics KPIs calculated: {kpis}")
    assert "avg_transit_time" in kpis
    assert "avg_logistics_cost" in kpis
    assert "avg_route_utilization" in kpis
    assert "avg_shipment_delay" in kpis
    assert "on_time_delivery_pct" in kpis
    assert "delayed_shipment_pct" in kpis
    assert "avg_shipments_per_day" in kpis
    
    # Assert values match nominal bounds
    assert kpis["on_time_delivery_pct"] > 0
    assert kpis["avg_logistics_cost"] > 0

    # 2. Verify Hub and RC Scorecards
    print("\n--- TESTING SCORECARD PERFORMANCE SCORES ---")
    hub_card = payload["hub_scorecard"]
    print(f"Hub scorecard: {hub_card}")
    assert len(hub_card) == 5
    for h in hub_card:
        assert 0.0 <= h["performance_score"] <= 100.0
        assert "capacity_utilization" in h
        assert "avg_logistics_cost" in h

    rc_card = payload["rc_scorecard"]
    print(f"Repair Center scorecard: {rc_card}")
    assert len(rc_card) == 3
    for rc in rc_card:
        assert 0.0 <= rc["performance_score"] <= 100.0
        assert "capacity_utilization" in rc
        assert "avg_processing_time" in rc

    # 3. Verify Delay and Cost Analysis Breakdowns
    print("\n--- TESTING COST & DELAY ANALYSES ---")
    da = payload["delay_analysis"]
    print(f"Delay analysis summary: {da}")
    assert "total_delays" in da
    assert "by_priority" in da
    assert "by_partner" in da
    
    ca = payload["cost_analysis"]
    print(f"Cost analysis summary: {ca}")
    assert "avg_cost" in ca
    assert "max_cost" in ca
    assert "min_cost" in ca
    assert "by_hub" in ca
    assert "by_category" in ca

    # 4. Verify Trend Analysis Series
    print("\n--- TESTING TIME SERIES TRENDS ---")
    trends = payload["trends"]
    assert "daily" in trends
    assert "monthly" in trends
    print(f"Loaded {len(trends['daily'])} daily trend elements.")
    print(f"Loaded {len(trends['monthly'])} monthly trend elements.")
    assert len(trends["daily"]) > 0

    # 5. Verify Filter Actions
    print("\n--- TESTING DYNAMIC FILTERS SUBSETTING ---")
    payload_filt = PerformanceService.get_performance_payload({"status": "MET"})
    print(f"On-time Delivery % for filtered MET status: {payload_filt['kpis']['on_time_delivery_pct']}%")
    assert payload_filt["kpis"]["on_time_delivery_pct"] == 100.0
    assert payload_filt["kpis"]["delayed_shipment_pct"] == 0.0

    print("\nAll Logistics Performance Monitoring tests passed successfully!")

if __name__ == "__main__":
    test_performance_suite()
