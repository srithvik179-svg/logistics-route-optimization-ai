from pydantic import BaseModel
from typing import Optional

class TransactionRecord(BaseModel):
    Transaction_ID: str
    Dispatch_Date: str
    Actual_Delivery_Date: str
    Origin_Hub: str
    Destination_Location: str
    Part_No: str
    Quantity: Optional[float] = None
    SLA_Breach: str
    Logistics_Cost_Total_USD: Optional[float] = None
    Route_Distance: Optional[float] = None

    @property
    def Order_Date(self) -> str:
        return self.Dispatch_Date

    @property
    def Delivery_Date(self) -> str:
        return self.Actual_Delivery_Date

    @property
    def Destination_Hub(self) -> str:
        return self.Destination_Location

    @property
    def Part_Number(self) -> str:
        return self.Part_No

    @property
    def SLA_Status(self) -> str:
        return self.SLA_Breach

    @property
    def Shipment_Cost(self) -> Optional[float]:
        return self.Logistics_Cost_Total_USD

class HubRecord(BaseModel):
    Hub_ID: str
    Hub_Name: str
    Latitude: float
    Longitude: float
    City: str
    Primary_Region: str

    @property
    def Region(self) -> str:
        return self.Primary_Region

class TPRRecord(BaseModel):
    """Represents a Third Party Logistics Partner or Repair Center Record."""
    TPR_ID: str
    TPR_Name: str
    Coverage_Region: Optional[str] = "Global"
    SLA_Compliance_Target: Optional[float] = 95.0
    Rating: Optional[float] = 4.5

class PartRecord(BaseModel):
    Part_No: str
    Part_Description: str
    Category: str
    Weight_Kg: float
    Volume_cm3: float

    @property
    def Part_Number(self) -> str:
        return self.Part_No

    @property
    def Part_Name(self) -> str:
        return self.Part_Description

    @property
    def Dimensions_Cm3(self) -> float:
        return self.Volume_cm3

class SummaryRecord(BaseModel):
    pass

