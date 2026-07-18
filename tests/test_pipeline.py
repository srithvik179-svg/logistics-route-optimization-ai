import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.services.repository import DataRepository
from backend.models.processed_dataset import PipelineReport, ProcessingSummary
from backend.processors.text_processor import TextProcessor
import pandas as pd

def test_pipeline_suite():
    print("Initializing Pipeline verification suite...")
    
    # 1. Instantiate repo and initialize (which automatically triggers pipeline)
    repo = DataRepository()
    repo.initialize()
    
    # Check that sheets are processed and cached
    assert repo.is_initialized() is True
    assert len(repo._processed_sheets) == 5
    
    # 2. Get and verify the pipeline report
    report = repo.get_pipeline_report()
    assert report is not None
    summary = report.summary
    
    print("\n--- GLOBAL PIPELINE SUMMARY ---")
    print(f"Status: {summary.status}")
    print(f"Quality Score: {summary.quality_score}%")
    print(f"Processing Duration: {summary.duration_ms} ms")
    print(f"Total Rows Processed: {summary.rows_processed}")
    print(f"Total Columns Processed: {summary.cols_processed}")
    print(f"Missing Values Handled: {summary.missing_values_handled}")
    print(f"Duplicates Removed: {summary.duplicates_removed}")
    print(f"Columns Converted: {len(summary.columns_converted)}")
    
    assert summary.status == "SUCCESS"
    assert summary.quality_score > 0
    assert summary.rows_processed > 0
    
    # Verify sheet specific processing
    print("\n--- SHEET SUMMARIES ---")
    for name, sh in report.sheet_summaries.items():
        print(f"Sheet '{name}': Rows={sh.rows_processed}, Nulls={sh.missing_values_handled}, Dups={sh.duplicates_removed}, Quality={sh.quality_score}%")
        assert sh.status == "SUCCESS"

    # 3. Verify specific processors:
    # A. Duplicates processor verification
    # Transactions sheet had 1 duplicate, which should be removed in processed_sheets
    raw_tx_rows = len(repo._sheets["Logistics_Transactions"])
    proc_tx_rows = len(repo._processed_sheets["Logistics_Transactions"])
    print(f"\nDuplicates Check: Raw rows = {raw_tx_rows}, Processed rows = {proc_tx_rows}")
    assert raw_tx_rows - proc_tx_rows == 1, "Duplicate row should have been removed!"
    
    # B. Date enrichment verification
    proc_tx_cols = list(repo._processed_sheets["Logistics_Transactions"].columns)
    print("\nEnriched Date Fields Check:")
    print("  Processed columns in Logistics_Transactions:")
    print(f"    {proc_tx_cols}")
    
    # Make sure Year, Month, etc. are added
    for date_attr in ["Year", "Month", "Quarter", "Week", "Day", "Day_Name"]:
        assert f"Order_Date_{date_attr}" in proc_tx_cols, f"Enriched field 'Order_Date_{date_attr}' missing!"
        assert f"Delivery_Date_{date_attr}" in proc_tx_cols, f"Enriched field 'Delivery_Date_{date_attr}' missing!"
    print("  Date enrichment fields are verified.")

    # C. Text normalization verification
    # Let's verify specific casing updates
    # We can create a mini test dataframe to test TextProcessor directly
    test_df = pd.DataFrame({
        "City": ["bangalore", "BENGALURU", "hyd", "secunderabad", "dallas tx"],
        "SLA_Status": ["met", "missed", "Met ", "Missed", "met"],
        "TPR_Name": ["tpr-01", "swift logico", "apex freight", "delta express", "tpr-02"]
    })
    
    print("\nText Normalization Verification on sample:")
    print("  Raw:")
    print(test_df)
    
    processed_test_df, mods = TextProcessor.process(test_df, "Hub_Location_Master")
    print("  Processed:")
    print(processed_test_df)
    
    # Assert Bengaluru conversion
    assert processed_test_df.loc[0, "City"] == "Bengaluru"
    assert processed_test_df.loc[1, "City"] == "Bengaluru"
    assert processed_test_df.loc[2, "City"] == "Hyderabad"
    assert processed_test_df.loc[3, "City"] == "Hyderabad"
    assert processed_test_df.loc[4, "City"] == "Dallas"
    
    # Assert SLA Status uppercase
    assert processed_test_df.loc[0, "SLA_Status"] == "MET"
    assert processed_test_df.loc[1, "SLA_Status"] == "MISSED"
    assert processed_test_df.loc[2, "SLA_Status"] == "MET"
    
    # Assert TPR code uppercase and title casing
    assert processed_test_df.loc[0, "TPR_Name"] == "TPR-01"
    assert processed_test_df.loc[1, "TPR_Name"] == "Swift Logico"
    
    print("  Text normalization successfully verified.")

    print("\nAll pipeline and processor tests passed successfully!")

if __name__ == "__main__":
    test_pipeline_suite()
