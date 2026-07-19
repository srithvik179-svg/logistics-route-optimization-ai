import os
from typing import Dict, List

# Base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Dataset Configuration
DEFAULT_DATASET_PATH = os.path.join(DATA_DIR, "Dell_Logistics_Route_Optimization.xlsx")

# Expected Sheets
REQUIRED_SHEETS = [
    "Logistics_Transactions",
    "Hub_Location_Master",
    "TPR_Master",
    "Parts_Master",
    "Summary_Dashboard"
]

# Expected Columns per Sheet (Based on actual Dell FutureMinds dataset schema)
EXPECTED_COLUMNS: Dict[str, List[str]] = {
    "Logistics_Transactions": [
        "Transaction_ID",
        "Dispatch_Date",
        "Actual_Delivery_Date",
        "Origin_Hub",
        "Destination_Location",
        "Part_No",
        "Quantity",
        "SLA_Breach",
        "Logistics_Cost_Total_USD"
    ],
    "Hub_Location_Master": [
        "Hub_ID",
        "Hub_Name",
        "Latitude",
        "Longitude",
        "City",
        "Primary_Region"
    ],
    "TPR_Master": [
        "TPR_ID",
        "TPR_Name"
    ],
    "Parts_Master": [
        "Part_No",
        "Part_Description",
        "Category",
        "Weight_Kg",
        "Volume_cm3"
    ],
    "Summary_Dashboard": []
}

# Column Data Types (for validation)
COLUMN_TYPES: Dict[str, Dict[str, str]] = {
    "Logistics_Transactions": {
        "Transaction_ID": "object",
        "Dispatch_Date": "datetime",
        "Actual_Delivery_Date": "datetime",
        "Origin_Hub": "object",
        "Destination_Location": "object",
        "Part_No": "object",
        "Quantity": "numeric",
        "SLA_Breach": "object",
        "Logistics_Cost_Total_USD": "numeric"
    },
    "Hub_Location_Master": {
        "Hub_ID": "object",
        "Hub_Name": "object",
        "Latitude": "numeric",
        "Longitude": "numeric",
        "City": "object",
        "Primary_Region": "object"
    },
    "TPR_Master": {
        "TPR_ID": "object",
        "TPR_Name": "object"
    },
    "Parts_Master": {
        "Part_No": "object",
        "Part_Description": "object",
        "Category": "object",
        "Weight_Kg": "numeric",
        "Volume_cm3": "numeric"
    },
    "Summary_Dashboard": {}
}

class SLAConfig:
    """Holds configuration parameters defining service level agreements.
    
    Can be updated or overridden by future AI agents or admin settings.
    """
    # Max allowed transit time in days
    TRANSIT_TIME_LIMIT: float = 3.0
    
    # Max allowed end-to-end delivery time in days
    DELIVERY_TIME_LIMIT: float = 4.0
    
    # Max allowed processing time at repair centers or intermediate nodes
    PROCESSING_TIME_LIMIT: float = 2.0
    
    # Max allowed hub handling delay
    HUB_HANDLING_TIME_LIMIT: float = 1.0
    
    # Max allowed repair center processing delay
    RC_PROCESSING_TIME_LIMIT: float = 3.0

