import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.services.repository import repository
from backend.services.analytics_service import AnalyticsService
from backend.services.metric_calculator import MetricCalculator

def test_analytics_suite():
    print("Initializing Analytics verification suite...")
    
    # Initialize repository singleton
    repository.initialize()
    
    df_tx = repository._processed_sheets["Logistics_Transactions"]
    df_hub = repository._processed_sheets["Hub_Location_Master"]
    tpr_sheet_name = "TPR_Master" if repository.sheet_exists("TPR_Master") else "Repair_Center_Master"
    df_tpr = repository._processed_sheets[tpr_sheet_name]
    
    # 1. Verify MetricCalculator methods
    print("\n--- KPI METRICS CHECK ---")
    tot_ship = MetricCalculator.calculate_total_shipments(df_tx)
    tot_cost = MetricCalculator.calculate_total_cost(df_tx)
    avg_cost = MetricCalculator.calculate_avg_cost(df_tx)
    avg_transit = MetricCalculator.calculate_avg_transit_days(df_tx)
    avg_inv = MetricCalculator.calculate_avg_inventory_level(df_tx)
    avg_hub_util = MetricCalculator.calculate_avg_hub_utilization(df_tx, df_hub)
    avg_tpr_util = MetricCalculator.calculate_avg_tpr_utilization(df_tx, df_tpr)
    
    print(f"Total Shipments: {tot_ship}")
    print(f"Total Cost: ${tot_cost:,.2f}")
    print(f"Average Cost: ${avg_cost:,.2f}")
    print(f"Average Transit Days: {avg_transit:.1f}")
    print(f"Average Inventory Level: {avg_inv}")
    print(f"Average Hub Utilization: {avg_hub_util}%")
    print(f"Average TPR Utilization: {avg_tpr_util}%")
    
    assert tot_ship == 11
    assert tot_cost > 0.0
    assert avg_cost > 0.0
    assert avg_transit == 2.0  # mock dates are spaced exactly 2 days apart: 7/1 -> 7/3, etc.
    assert avg_inv > 0.0
    assert avg_hub_util > 0.0
    assert avg_tpr_util > 0.0
    
    # 2. Verify AnalyticsService payload structure
    print("\n--- PAYLOAD STRUCTURE CHECK ---")
    payload = AnalyticsService.get_dashboard_payload()
    
    assert "kpis" in payload
    assert "summary_info" in payload
    assert "distributions" in payload
    assert "time_series" in payload
    
    print("KPI keys in payload:")
    print(f"  {list(payload['kpis'].keys())}")
    
    print("\nDistributions keys in payload:")
    print(f"  {list(payload['distributions'].keys())}")
    
    # Check sheet metrics
    dists = payload["distributions"]
    assert len(dists["flow_types"]) > 0
    assert len(dists["priorities"]) > 0
    assert len(dists["partners"]) > 0
    assert len(dists["part_categories"]) > 0
    assert len(dists["sla_statuses"]) > 0
    assert len(dists["hub_types"]) > 0
    assert len(dists["tpr_locations"]) > 0
    
    print("\nAll Executive Dashboard Analytics tests passed successfully!")

if __name__ == "__main__":
    test_analytics_suite()
