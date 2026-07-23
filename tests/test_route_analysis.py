import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.services.repository import repository
from backend.services.route_analysis_service import RouteAnalysisService

def test_route_analysis_suite():
    print("Initializing Route Analysis & Network Intelligence verification suite...")
    
    # Initialize repository
    repository.initialize()
    
    # 1. Fetch default route analysis payload
    print("\n--- TESTING ROUTE ANALYSIS PAYLOAD (NO FILTERS) ---")
    payload = RouteAnalysisService.get_route_analysis_payload({})
    
    assert "overview" in payload
    assert "routes" in payload
    assert "bottlenecks" in payload
    assert "flows" in payload
    assert "graph" in payload
    assert "heatmap" in payload
    
    print(f"Overview stats: {payload['overview']}")
    print(f"Total Routes: {len(payload['routes'])}")
    print(f"Total Bottlenecks: {len(payload['bottlenecks'])}")
    
    assert payload["overview"]["total_active_routes"] == len(payload["routes"])
    assert len(payload["routes"]) > 0
    
    # Check Route details structure
    r0 = payload["routes"][0]
    print(f"Route sample: {r0}")
    assert "origin" in r0
    assert "destination" in r0
    assert "distance" in r0
    assert "transit_time" in r0
    assert "shipment_count" in r0
    assert "avg_cost" in r0
    assert "is_bottleneck" in r0
    assert "priority_dist" in r0
    assert "status_dist" in r0

    # 2. Test Bottleneck Rules
    print("\n--- TESTING BOTTLENECK CLASSIFICATION RULES ---")
    bottleneck_count = len(payload["bottlenecks"])
    print(f"Found {bottleneck_count} routes marked as bottlenecks.")
    for b in payload["bottlenecks"]:
        assert b["is_bottleneck"] is True
        print(f"Bottleneck Route {b['origin']} -> {b['destination']} reasons: {b['bottleneck_reason']}")
        assert len(b["bottleneck_reason"]) > 0

    # 3. Test Flow Analysis (Inbound vs Outbound per Hub)
    print("\n--- TESTING HUB FLOW IMPERFECT BALANCE ---")
    flows = payload["flows"]
    assert "hubs" in flows
    assert "segments" in flows
    
    for hub, hub_stats in flows["hubs"].items():
        print(f"Hub {hub} Flows: Inbound={hub_stats['inbound']}, Outbound={hub_stats['outbound']}, Imbalance={hub_stats['net']}")
        assert hub_stats["inbound"] >= 0
        assert hub_stats["outbound"] >= 0
        assert hub_stats["net"] == hub_stats["outbound"] - hub_stats["inbound"]

    # 4. Test Dynamic Filtering
    print("\n--- TESTING ROUTE ANALYSIS FILTERS ---")
    payload_high = RouteAnalysisService.get_route_analysis_payload({"priority": "High Priority"})
    print(f"Total routes with High Priority shipments: {len(payload_high['routes'])}")
    # Verify average distance is higher or matches filtering scope
    
    payload_hub_a = RouteAnalysisService.get_route_analysis_payload({"hub": "HUB-BLR"})
    print(f"Total routes touching HUB-BLR: {len(payload_hub_a['routes'])}")
    for r in payload_hub_a["routes"]:
        assert r["origin"] == "HUB-BLR" or r["destination"] == "HUB-BLR"

    print("\nAll Route Analysis & Network Intelligence tests passed successfully!")

if __name__ == "__main__":
    test_route_analysis_suite()
