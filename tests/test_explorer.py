import os
import sys
import pandas as pd

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.services.repository import DataRepository
from backend.services.explorer_service import ExplorerService

def test_explorer_suite():
    print("Initializing Explorer verification suite...")
    
    # Initialize repository
    repo = DataRepository()
    repo.initialize()
    
    # 1. Test memory formatting
    df_tx = repo._processed_sheets["Logistics_Transactions"]
    memory_str = ExplorerService.get_memory_usage(df_tx)
    print(f"Memory string formatted: {memory_str}")
    assert "KB" in memory_str or "Bytes" in memory_str
    
    # 2. Test column profiling metrics
    print("\nProfiling column 'Origin_Hub' in 'Logistics_Transactions':")
    profile = ExplorerService.profile_column(df_tx, "Origin_Hub")
    print(f"  Type: {profile['data_type']}")
    print(f"  Null Count: {profile['null_count']}")
    print(f"  Duplicate Count: {profile['duplicate_count']}")
    print(f"  Unique Count: {profile['unique_count']}")
    print(f"  Samples: {profile['sample_values']}")
    
    assert profile["column_name"] == "Origin_Hub"
    assert profile["data_type"] == "text"
    assert profile["unique_count"] > 0
    assert len(profile["sample_values"]) > 0
    
    # 3. Test global search query
    print("\nTesting Global Search across columns (query: 'MISSED'):")
    df_search, total_search = ExplorerService.query_dataframe(df_tx, search_query="MISSED")
    print(f"  Matches found: {total_search}")
    for idx, r in df_search.iterrows():
        print(f"    Tx: {r['Transaction_ID']}, SLA: {r['SLA_Status']}")
        assert "MISSED" in str(r['SLA_Status']).upper()
        
    # 4. Test stackable filtering
    print("\nTesting Stackable Filters (Origin_Hub='Bengaluru', Route_Distance > 150.0):")
    filters = [
        {"column": "Origin_Hub", "operator": "equals", "value": "Bengaluru"},
        {"column": "Route_Distance", "operator": ">", "value": "150.0"}
    ]
    df_filter, total_filter = ExplorerService.query_dataframe(df_tx, filters=filters)
    print(f"  Matches found: {total_filter}")
    for idx, r in df_filter.iterrows():
        print(f"    Tx: {r['Transaction_ID']}, Origin: {r['Origin_Hub']}, Distance: {r['Route_Distance']}")
        assert r['Origin_Hub'] == "Bengaluru"
        assert float(r['Route_Distance']) > 150.0
        
    # 5. Test sorting and pagination
    print("\nTesting Sorting and Pagination (page=1, page_size=3, sort_by='Shipment_Cost', sort_order='desc'):")
    df_sorted, total_sorted = ExplorerService.query_dataframe(
        df_tx, 
        page=1, 
        page_size=3, 
        sort_by="Shipment_Cost", 
        sort_order="desc"
    )
    print(f"  Total records matching: {total_sorted}")
    print(f"  Top 3 high-cost transactions on page 1:")
    prev_cost = float('inf')
    for idx, r in df_sorted.iterrows():
        cost = float(r['Shipment_Cost'])
        print(f"    Tx: {r['Transaction_ID']}, Cost: {cost}")
        assert cost <= prev_cost
        prev_cost = cost
    assert len(df_sorted) == 3
    
    print("\nAll Dataset Explorer tests passed successfully!")

if __name__ == "__main__":
    test_explorer_suite()
