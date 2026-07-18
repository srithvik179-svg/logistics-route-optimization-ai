import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.config import DEFAULT_DATASET_PATH
from backend.services.dataset_loader import DatasetLoader
from backend.validators.dataset_validator import DatasetValidator

def test_dataset_pipeline():
    print("Initializing test dataset pipeline...")
    print(f"Target dataset path: {DEFAULT_DATASET_PATH}")
    
    loader = DatasetLoader(DEFAULT_DATASET_PATH)
    
    # 1. Get metadata
    metadata = loader.get_metadata()
    print("\n--- METADATA ---")
    print(f"Exists: {metadata.exists}")
    print(f"File Size (Bytes): {metadata.file_size_bytes}")
    print(f"Sheet Names: {metadata.sheet_names}")
    print(f"Is Corrupt: {metadata.is_corrupt}")
    print(f"Is Empty: {metadata.is_empty}")
    
    assert metadata.exists is True, "Mock dataset should exist!"
    assert len(metadata.sheet_names) == 5, "Mock dataset should contain exactly 5 sheets!"
    
    # 2. Load sheets
    metadata, sheets_data = loader.load()
    print("\n--- LOADED SHEETS ---")
    for name, df in sheets_data.items():
        print(f"Sheet '{name}': {len(df)} rows, {len(df.columns)} columns")
        
    assert "Logistics_Transactions" in sheets_data, "Logistics_Transactions sheet should be loaded!"
    
    # 3. Validate
    report = DatasetValidator.validate(metadata, sheets_data)
    print("\n--- VALIDATION REPORT ---")
    print(f"Overall Valid: {report.is_valid}")
    print(f"Global Errors: {report.global_errors}")
    print(f"Global Warnings: {report.global_warnings}")
    
    # Check sheet level issues
    for sheet_name, sheet_report in report.sheets.items():
        print(f"\nSheet '{sheet_name}' validation details:")
        print(f"  Exists: {sheet_report.exists}")
        print(f"  Row Count: {sheet_report.row_count}")
        print(f"  Duplicate Rows: {sheet_report.duplicate_rows}")
        print(f"  Empty Rows: {sheet_report.empty_rows}")
        print(f"  Errors: {sheet_report.errors}")
        print(f"  Warnings: {sheet_report.warnings}")

    print("\nAll pipeline checks completed successfully!")

if __name__ == "__main__":
    test_dataset_pipeline()
