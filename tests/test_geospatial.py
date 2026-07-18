import os
import sys
import pandas as pd

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.services.repository import repository
from backend.services.geospatial_service import GeospatialService

def test_geospatial_suite():
    print("Initializing Geospatial verification suite...")
    
    # Initialize repository
    repository.initialize()
    
    # 1. Fetch default map payload (no filters)
    print("\n--- TESTING MAP PAYLOAD (NO FILTERS) ---")
    payload = GeospatialService.get_network_payload({})
    
    assert "hubs" in payload
    assert "repair_centers" in payload
    assert "flows" in payload
    assert "summary" in payload
    
    print(f"Loaded {len(payload['hubs'])} Hubs.")
    print(f"Loaded {len(payload['repair_centers'])} Repair Centers.")
    print(f"Loaded {len(payload['flows'])} Flow route lines.")
    
    # Assert counts
    assert len(payload["hubs"]) == 5
    assert len(payload["repair_centers"]) == 3
    assert len(payload["flows"]) > 0
    
    # Check Hub schema
    h0 = payload["hubs"][0]
    print(f"Hub marker sample: {h0}")
    assert "id" in h0
    assert "name" in h0
    assert "lat" in h0
    assert "lon" in h0
    assert "capacity" in h0
    assert "utilization" in h0
    assert "inventory_summary" in h0
    
    # Check RC schema
    rc0 = payload["repair_centers"][0]
    print(f"Repair Center marker sample: {rc0}")
    assert "id" in rc0
    assert "name" in rc0
    assert "lat" in rc0
    assert "lon" in rc0
    assert "capacity" in rc0
    assert "utilization" in rc0
    assert "supported_parts" in rc0
    
    # Check Flow schema
    f0 = payload["flows"][0]
    print(f"Flow line vector sample: {f0}")
    assert "origin_id" in f0
    assert "destination_id" in f0
    assert "origin_lat" in f0
    assert "origin_lon" in f0
    assert "dest_lat" in f0
    assert "dest_lon" in f0
    assert "shipment_count" in f0
    assert "flow_type" in f0
    assert "avg_transit_time" in f0
    assert "avg_cost" in f0

    # 2. Test Dynamic Map Filtering: Filter by status='MET'
    print("\n--- TESTING DYNAMIC MAP FILTERS ---")
    payload_met = GeospatialService.get_network_payload({"status": "MET"})
    print(f"Visible shipments with status='MET': {payload_met['summary']['visible_shipments']}")
    assert payload_met["summary"]["visible_shipments"] == 8
    
    # Filter by Hub 'HUB-A'
    payload_hub = GeospatialService.get_network_payload({"hub": "HUB-A"})
    print(f"Visible shipments for HUB-A: {payload_hub['summary']['visible_shipments']}")
    assert payload_hub["summary"]["visible_shipments"] > 0
    
    # Filter by Date range
    payload_date = GeospatialService.get_network_payload({
        "start_date": "2026-07-01",
        "end_date": "2026-07-05"
    })
    print(f"Visible shipments between 2026-07-01 and 2026-07-05: {payload_date['summary']['visible_shipments']}")
    assert payload_date["summary"]["visible_shipments"] > 0

    # 3. Test Registry Fallback Behavior
    print("\n--- TESTING COORDINATES REGISTRY FALLBACK ---")
    # Simulate a hub lacking coordinate values in DataFrame
    df_hub_incomplete = pd.DataFrame([{
        "Hub_ID": "HUB-A",
        "Hub_Name": "Austin Hub",
        "Latitude": float("nan"),
        "Longitude": float("nan"),
        "City": "Austin",
        "Region": "TX"
    }])
    # Patch sheet in repository to test fallback trigger
    orig_sheet = repository._processed_sheets["Hub_Location_Master"]
    repository._processed_sheets["Hub_Location_Master"] = df_hub_incomplete
    
    try:
        payload_fb = GeospatialService.get_network_payload({})
        hub_a_resolved = [h for h in payload_fb["hubs"] if h["id"] == "HUB-A"][0]
        print(f"Incomplete Hub HUB-A resolved coordinate: ({hub_a_resolved['lat']}, {hub_a_resolved['lon']})")
        assert hub_a_resolved["lat"] == 30.2672
        assert hub_a_resolved["lon"] == -97.7431
    finally:
        # Restore sheet
        repository._processed_sheets["Hub_Location_Master"] = orig_sheet

    print("\nAll Geospatial Network Map tests passed successfully!")

if __name__ == "__main__":
    test_geospatial_suite()
