from pydantic import BaseModel
from typing import Optional

class TransactionRecord(BaseModel):
    Transaction_ID: str
    Order_Date: str
    Delivery_Date: str
    Origin_Hub: str
    Destination_Hub: str
    Part_Number: str
    Quantity: Optional[float] = None
    SLA_Status: str
    Shipment_Cost: Optional[float] = None
    Route_Distance: Optional[float] = None

class HubRecord(BaseModel):
    Hub_ID: str
    Hub_Name: str
    Latitude: float
    Longitude: float
    City: str
    Region: str

class TPRRecord(BaseModel):
    """Represents a Third Party Logistics Partner or Repair Center Record."""
    TPR_ID: str
    TPR_Name: str
    Coverage_Region: str
    SLA_Compliance_Target: float
    Rating: float

class PartRecord(BaseModel):
    Part_Number: str
    Part_Name: str
    Category: str
    Weight_Kg: float
    Dimensions_Cm3: float

class SummaryRecord(BaseModel):
    Metric_Name: str
    Value: str
