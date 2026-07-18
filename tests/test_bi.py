import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.services.repository import repository
from backend.services.bi_service import BIService

def test_bi_suite():
    print("Initializing BI verification suite...")
    
    # Initialize repository singleton
    repository.initialize()
    
    # Get raw transaction table count (filtered is compared to this)
    df_tx_raw = repository._processed_sheets["Logistics_Transactions"]
    raw_count = len(df_tx_raw)
    print(f"Loaded raw transactions count: {raw_count}")
    assert raw_count == 11
    
    # 1. Test Filter: SLA Status Met
    print("\n--- TESTING GLOBAL FILTERS ---")
    df_met = BIService.apply_filters(df_tx_raw, {"status": "MET"})
    print(f"SLA Status 'MET' filter count: {len(df_met)}")
    assert len(df_met) == 8
    
    # Test Filter: Hub
    df_hub_a = BIService.apply_filters(df_tx_raw, {"hub": "HUB-A"})
    print(f"Hub 'HUB-A' (origin or dest) count: {len(df_hub_a)}")
    assert len(df_hub_a) > 0
    
    # Test Filter: Flow Type
    df_flow = BIService.apply_filters(df_tx_raw, {"flow_type": "Hub-to-Hub Transfer"})
    print(f"Flow 'Hub-to-Hub Transfer' count: {len(df_flow)}")
    assert len(df_flow) == 11
    
    # 2. Test Compare Entities: compare HUB-A against HUB-B
    print("\n--- TESTING COMPARATIVE ANALYTICS ---")
    comp = BIService.compare_entities("hub", "HUB-A", "HUB-B", {})
    assert "entity_a" in comp
    assert "entity_b" in comp
    print("HUB-A stats:")
    print(f"  Shipments: {comp['entity_a']['count']}")
    print(f"  Cost: ${comp['entity_a']['cost']:,.2f}")
    print(f"  SLA Rate: {comp['entity_a']['sla_rate']:.1f}%")
    print(f"  Transit Days: {comp['entity_a']['avg_transit']:.1f} Days")
    
    # 3. Test Rankings: Top and Bottom lists
    print("\n--- TESTING TOP & BOTTOM PERFORMERS ---")
    payload = BIService.get_dashboard_payload({})
    performers = payload["performers"]
    assert "top_partners" in performers
    assert "top_hubs" in performers
    assert "top_tprs" in performers
    assert "bottom_hubs" in performers
    assert "bottom_tprs" in performers
    print(f"Top Partners: {[p['Logistics_Partner'] for p in performers['top_partners']]}")
    print(f"Top Hubs: {[h['Hub_ID'] for h in performers['top_hubs']]}")
    
    # 4. Test Export report
    print("\n--- TESTING CSV REPORT EXPORTS ---")
    csv_tx = BIService.generate_csv_report({}, "transactions")
    assert csv_tx.startswith("Transaction_ID,Order_Date,Delivery_Date")
    print("Transactions CSV preview:")
    print("\n".join(csv_tx.split("\n")[:4]))
    
    csv_kpis = BIService.generate_csv_report({}, "kpis")
    assert "Metric,Value" in csv_kpis
    print("KPIs CSV preview:")
    print(csv_kpis.strip())
    
    print("\nAll Business Intelligence tests passed successfully!")

if __name__ == "__main__":
    test_bi_suite()
