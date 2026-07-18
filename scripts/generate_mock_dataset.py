import os
import pandas as pd
from datetime import datetime, timedelta

# Define output path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "Dell_Logistics_Route_Optimization.xlsx")

def generate_mock_dataset():
    print(f"Creating mock dataset at: {OUTPUT_FILE}")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 1. Logistics_Transactions
    # Generate some records
    txn_data = {
        "Transaction_ID": [f"TXN-{1000 + i}" for i in range(10)],
        "Order_Date": [datetime(2026, 7, 1) + timedelta(days=i) for i in range(10)],
        "Delivery_Date": [datetime(2026, 7, 3) + timedelta(days=i) for i in range(10)],
        "Origin_Hub": ["HUB-A", "HUB-B", "HUB-C", "HUB-A", "HUB-D", "HUB-E", "HUB-B", "HUB-C", "HUB-A", "HUB-E"],
        "Destination_Hub": ["HUB-B", "HUB-C", "HUB-D", "HUB-E", "HUB-A", "HUB-B", "HUB-C", "HUB-D", "HUB-E", "HUB-A"],
        "Part_Number": ["PART-001", "PART-002", "PART-001", "PART-003", "PART-002", "PART-003", "PART-001", "PART-002", "PART-001", "PART-003"],
        "Quantity": [10, 5, 12, 8, 3, 15, 6, 2, 20, 7],
        "SLA_Status": ["MET", "MET", "MISSED", "MET", "MET", "MISSED", "MET", "MET", "MET", "MET"],
        "Shipment_Cost": [150.50, 85.00, 320.00, 210.25, 95.00, 450.00, 110.00, 60.50, 400.00, 180.75],
        "Route_Distance": [120.5, 65.2, 450.0, 280.4, 90.0, 620.1, 105.5, 45.2, 380.0, 210.3]
    }
    df_txn = pd.DataFrame(txn_data)
    
    # Add intentional validation warnings/errors
    # 1. A true duplicate row (duplicate of row index 1)
    dup_row = df_txn.iloc[1:2].copy()
    df_txn = pd.concat([df_txn, dup_row], ignore_index=True)
    
    # 2. A separate row with missing values (NaN) in a few columns
    missing_row = df_txn.iloc[2:3].copy()
    missing_row.loc[missing_row.index[0], "Transaction_ID"] = "TXN-1010"
    missing_row.loc[missing_row.index[0], "Quantity"] = None
    missing_row.loc[missing_row.index[0], "Route_Distance"] = None
    df_txn = pd.concat([df_txn, missing_row], ignore_index=True)
    
    # 3. An entirely empty row (filled with NaNs)
    # To prevent pandas read_excel from stripping it entirely, we will write it,
    # but note that pandas Excel parser might still strip it. This is standard behavior.
    empty_row = pd.DataFrame([{col: None for col in df_txn.columns}])
    df_txn = pd.concat([df_txn, empty_row], ignore_index=True)

    # 2. Hub_Location_Master
    hub_data = {
        "Hub_ID": ["HUB-A", "HUB-B", "HUB-C", "HUB-D", "HUB-E"],
        "Hub_Name": ["Austin Hub", "Houston Hub", "Dallas Hub", "San Antonio Hub", "El Paso Hub"],
        "Latitude": [30.2672, 29.7604, 32.7767, 29.4241, 31.7619],
        "Longitude": [-97.7431, -95.3698, -96.7970, -98.4936, -106.4850],
        "City": ["Austin", "Houston", "Dallas", "San Antonio", "El Paso"],
        "Region": ["TX", "TX", "TX", "TX", "TX"]
    }
    df_hub = pd.DataFrame(hub_data)

    # 3. TPR_Master (Third-Party Representatives)
    tpr_data = {
        "TPR_ID": ["TPR-001", "TPR-002", "TPR-003"],
        "TPR_Name": ["Swift LogiCo", "Apex Freight", "LoneStar Delivery"],
        "Coverage_Region": ["South-Central", "National", "West-Texas"],
        "SLA_Compliance_Target": [0.95, 0.98, 0.92],
        "Rating": [4.7, 4.9, 4.1]
    }
    df_tpr = pd.DataFrame(tpr_data)

    # 4. Parts_Master
    parts_data = {
        "Part_Number": ["PART-001", "PART-002", "PART-003"],
        "Part_Name": ["Latitude Motherboard", "Precision Power Supply", "OptiPlex Chassis"],
        "Category": ["Electronics", "Power", "Chassis"],
        "Weight_Kg": [0.85, 2.10, 4.50],
        "Dimensions_Cm3": [120.0, 450.0, 1800.0]
    }
    df_parts = pd.DataFrame(parts_data)

    # 5. Summary_Dashboard
    summary_data = {
        "Metric_Name": ["Total Transaction Count", "Total Hubs Active", "Top Performing TPR"],
        "Value": ["10", "5", "Apex Freight"]
    }
    df_summary = pd.DataFrame(summary_data)

    # Write to Excel
    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        df_txn.to_excel(writer, sheet_name="Logistics_Transactions", index=False)
        df_hub.to_excel(writer, sheet_name="Hub_Location_Master", index=False)
        df_tpr.to_excel(writer, sheet_name="TPR_Master", index=False)
        df_parts.to_excel(writer, sheet_name="Parts_Master", index=False)
        df_summary.to_excel(writer, sheet_name="Summary_Dashboard", index=False)
        
    print("Mock dataset generated successfully.")

if __name__ == "__main__":
    generate_mock_dataset()
