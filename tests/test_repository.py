import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.services.repository import DataRepository
from backend.services.state_manager import state_manager
from backend.models.repository_models import (
    TransactionRecord,
    HubRecord,
    TPRRecord,
    PartRecord,
    SummaryRecord
)

def test_repository_suite():
    print("Initializing Repository verification suite...")
    
    # 1. Instantiate repo
    repo = DataRepository()
    assert repo.is_initialized() is False, "Repository should not be initialized on instantiation."
    
    # 2. Run initialization
    repo.initialize()
    assert repo.is_initialized() is True, "Repository should be initialized after calling initialize()."
    
    # Check state manager flags
    state = state_manager.get_state()
    print("\n--- STATE FLAGS ---")
    print(f"Dataset Loaded: {state.dataset_loaded}")
    print(f"Validation Passed: {state.validation_passed}")
    print(f"Repository Ready: {state.repository_ready}")
    print(f"Application Ready: {state.application_ready}")
    print(f"Repository Health: {state.repository_health}")
    print(f"Last Load Time: {state.last_load_time}")
    
    assert state.dataset_loaded is True
    assert state.repository_ready is True
    assert state.application_ready is True
    
    # 3. Test list_available_sheets
    sheets = repo.list_available_sheets()
    print("\n--- AVAILABLE SHEETS ---")
    print(sheets)
    assert len(sheets) == 5
    assert "Logistics_Transactions" in sheets
    
    # 4. Test row and column counts
    tx_rows = repo.get_row_count("Logistics_Transactions")
    tx_cols = repo.get_column_count("Logistics_Transactions")
    print(f"\nTransactions sheet stats: Rows = {tx_rows}, Cols = {tx_cols}")
    assert tx_rows > 0
    assert tx_cols == 10
    
    # 5. Test missing sheet behavior
    print("\nTesting missing sheet access...")
    missing_count = repo.get_row_count("Non_Existent_Sheet")
    assert missing_count == 0
    missing_data = repo.get_sheet("Non_Existent_Sheet")
    assert missing_data == [], "Missing sheet should return empty list."
    
    # 6. Verify typed data accessors
    print("\nTesting typed accessors...")
    
    # Transactions
    txns = repo.get_all_transactions()
    print(f"  Loaded {len(txns)} transactions.")
    assert len(txns) > 0
    assert isinstance(txns[0], TransactionRecord)
    print("    Sample transaction:", txns[0].model_dump())
    
    # Hubs
    hubs = repo.get_hubs()
    print(f"  Loaded {len(hubs)} hubs.")
    assert len(hubs) > 0
    assert isinstance(hubs[0], HubRecord)
    
    # Repair Centers / TPR
    tprs = repo.get_repair_centers()
    print(f"  Loaded {len(tprs)} repair centers (TPRs).")
    assert len(tprs) > 0
    assert isinstance(tprs[0], TPRRecord)
    
    # Parts
    parts = repo.get_parts()
    print(f"  Loaded {len(parts)} parts.")
    assert len(parts) > 0
    assert isinstance(parts[0], PartRecord)
    
    # Summary
    summary = repo.get_summary()
    print(f"  Loaded {len(summary)} summary KPIs.")
    assert len(summary) > 0
    assert isinstance(summary[0], SummaryRecord)
    
    print("\nAll Repository Layer tests passed successfully!")

if __name__ == "__main__":
    test_repository_suite()
