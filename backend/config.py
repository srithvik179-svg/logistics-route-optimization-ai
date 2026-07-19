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

# Expected Columns per Sheet
EXPECTED_COLUMNS: Dict[str, List[str]] = {
    "Logistics_Transactions": [
        "Transaction_ID",
        "Order_Date",
        "Delivery_Date",
        "Origin_Hub",
        "Destination_Hub",
        "Part_Number",
        "Quantity",
        "SLA_Status",
        "Shipment_Cost",
        "Route_Distance"
    ],
    "Hub_Location_Master": [
        "Hub_ID",
        "Hub_Name",
        "Latitude",
        "Longitude",
        "City",
        "Region"
    ],
    "TPR_Master": [
        "TPR_ID",
        "TPR_Name",
        "Coverage_Region",
        "SLA_Compliance_Target",
        "Rating"
    ],
    "Parts_Master": [
        "Part_Number",
        "Part_Name",
        "Category",
        "Weight_Kg",
        "Dimensions_Cm3"
    ],
    "Summary_Dashboard": [
        "Metric_Name",
        "Value"
    ]
}

# Column Data Types (for validation)
COLUMN_TYPES: Dict[str, Dict[str, str]] = {
    "Logistics_Transactions": {
        "Transaction_ID": "object",
        "Order_Date": "datetime",
        "Delivery_Date": "datetime",
        "Origin_Hub": "object",
        "Destination_Hub": "object",
        "Part_Number": "object",
        "Quantity": "numeric",
        "SLA_Status": "object",
        "Shipment_Cost": "numeric",
        "Route_Distance": "numeric"
    },
    "Hub_Location_Master": {
        "Hub_ID": "object",
        "Hub_Name": "object",
        "Latitude": "numeric",
        "Longitude": "numeric",
        "City": "object",
        "Region": "object"
    },
    "TPR_Master": {
        "TPR_ID": "object",
        "TPR_Name": "object",
        "Coverage_Region": "object",
        "SLA_Compliance_Target": "numeric",
        "Rating": "numeric"
    },
    "Parts_Master": {
        "Part_Number": "object",
        "Part_Name": "object",
        "Category": "object",
        "Weight_Kg": "numeric",
        "Dimensions_Cm3": "numeric"
    },
    "Summary_Dashboard": {
        "Metric_Name": "object",
        "Value": "object"
    }
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

