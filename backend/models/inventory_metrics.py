"""Pydantic models defining typed schemas for all inventory analytics outputs."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class InventoryOverviewMetrics(BaseModel):
    """Top-level inventory KPIs across the logistics network."""
    total_inventory: float = Field(description="Sum of all current inventory stock levels across all locations")
    avg_inventory: float = Field(description="Mean current stock level per location-part pair")
    min_inventory: float = Field(description="Minimum current stock level recorded at any single location-part pair")
    max_inventory: float = Field(description="Maximum current stock level recorded at any single location-part pair")
    inventory_variance: float = Field(description="Variance of inventory stock levels")
    inventory_std_deviation: float = Field(description="Standard deviation of inventory stock levels")
    inventory_per_hub: Dict[str, float] = Field(default_factory=dict, description="Aggregate inventory levels per hub")
    inventory_per_repair_center: Dict[str, float] = Field(default_factory=dict, description="Aggregate inventory levels per repair center")
    inventory_per_part_category: Dict[str, float] = Field(default_factory=dict, description="Aggregate inventory levels per part category")
    inventory_per_region: Dict[str, float] = Field(default_factory=dict, description="Aggregate inventory levels per region")
    inventory_per_partner: Dict[str, float] = Field(default_factory=dict, description="Aggregate inventory levels per logistics partner")


class InventoryMovementDimension(BaseModel):
    """Detailed incoming/outgoing movement metrics for a specific dimension."""
    incoming: float = Field(description="Sum of incoming quantity")
    outgoing: float = Field(description="Sum of outgoing quantity")
    net_movement: float = Field(description="Incoming minus outgoing quantity")


class InventoryMovement(BaseModel):
    """Container for all inventory movement breakdown analyses."""
    incoming_total: float = Field(description="Total incoming units across the network")
    outgoing_total: float = Field(description="Total outgoing units across the network")
    by_hub: Dict[str, InventoryMovementDimension] = Field(default_factory=dict, description="Movement aggregated by hub")
    by_region: Dict[str, InventoryMovementDimension] = Field(default_factory=dict, description="Movement aggregated by region")
    by_part: Dict[str, InventoryMovementDimension] = Field(default_factory=dict, description="Movement aggregated by part number")
    by_month: Dict[str, InventoryMovementDimension] = Field(default_factory=dict, description="Movement aggregated by month")
    by_quarter: Dict[str, InventoryMovementDimension] = Field(default_factory=dict, description="Movement aggregated by quarter")


class StockLevelItem(BaseModel):
    """Represents an item-location stock classification entry."""
    location: str = Field(description="Hub or Repair Center ID")
    part_number: str = Field(description="Part number")
    stock_level: float = Field(description="Current on-hand stock quantity")


class StockAnalysis(BaseModel):
    """Stock levels classification and moving parts analysis."""
    high_stock_items: List[StockLevelItem] = Field(default_factory=list, description="Items with stock level > 120")
    low_stock_items: List[StockLevelItem] = Field(default_factory=list, description="Items with 10 < stock level <= 50")
    critical_stock_items: List[StockLevelItem] = Field(default_factory=list, description="Items with 0 < stock level <= 10")
    zero_stock_items: List[StockLevelItem] = Field(default_factory=list, description="Items with stock level == 0")
    fast_moving_parts: List[str] = Field(default_factory=list, description="Part numbers with highest transaction frequency")
    slow_moving_parts: List[str] = Field(default_factory=list, description="Part numbers with lowest transaction frequency")


class UtilizationAnalysis(BaseModel):
    """Hub, repair center capacities and utilization rates."""
    hub_utilization: Dict[str, float] = Field(default_factory=dict, description="Hub occupancy rates (stock / capacity)")
    repair_center_utilization: Dict[str, float] = Field(default_factory=dict, description="Repair center occupancy rates")
    avg_inventory_capacity: float = Field(description="Average storage capacity across all nodes")
    inventory_occupancy: float = Field(description="Overall network occupancy percentage")
    inventory_turnover_ratio: float = Field(description="Total outgoing units divided by average inventory")


class RankingEntry(BaseModel):
    """A generic rank container entry."""
    rank: int = Field(description="Position in ranking (1-indexed)")
    name: str = Field(description="Entity name")
    value: float = Field(description="Metric value used for sorting")


class InventoryRankings(BaseModel):
    """Container for inventory rankings."""
    top_inventory_hubs: List[RankingEntry] = Field(default_factory=list)
    lowest_inventory_hubs: List[RankingEntry] = Field(default_factory=list)
    top_repair_centers: List[RankingEntry] = Field(default_factory=list)
    top_moving_parts: List[RankingEntry] = Field(default_factory=list)
    slowest_moving_parts: List[RankingEntry] = Field(default_factory=list)


class InventoryAnomaly(BaseModel):
    """A single detected inventory anomaly/outlier."""
    location: str = Field(description="Hub or Repair Center ID")
    part_number: Optional[str] = Field(None, description="Part number (if applicable)")
    metric_value: float = Field(description="The value that triggered the outlier")
    anomaly_type: str = Field(description="'spike', 'drop', 'abnormal', 'overstock', or 'understock'")
    description: str = Field(description="Human readable explanation")


class InventoryOutliers(BaseModel):
    """Container for all inventory anomalies and outlier detections."""
    spikes: List[InventoryAnomaly] = Field(default_factory=list, description="Unexpected inventory transaction spikes")
    drops: List[InventoryAnomaly] = Field(default_factory=list, description="Unexpected inventory transaction drops")
    abnormal_levels: List[InventoryAnomaly] = Field(default_factory=list, description="Abnormal node stock levels (IQR-based)")
    potential_overstock: List[InventoryAnomaly] = Field(default_factory=list, description="Nodes exceeding 90% capacity")
    potential_understock: List[InventoryAnomaly] = Field(default_factory=list, description="Nodes falling below 15 units")
    total_anomalies: int = Field(0, description="Total count of unique anomalies detected")


class InventoryTrendPoint(BaseModel):
    """A single trend point representing inventory levels over a time bucket."""
    period: str = Field(description="Period label (date, week, month, or quarter)")
    avg_stock_level: float = Field(description="Mean stock level across all active parts in this period")
    incoming_units: float = Field(description="Total units received in this period")
    outgoing_units: float = Field(description="Total units shipped in this period")


class InventoryTrends(BaseModel):
    """Container for daily, weekly, monthly, quarterly inventory trends."""
    daily: List[InventoryTrendPoint] = Field(default_factory=list)
    weekly: List[InventoryTrendPoint] = Field(default_factory=list)
    monthly: List[InventoryTrendPoint] = Field(default_factory=list)
    quarterly: List[InventoryTrendPoint] = Field(default_factory=list)


class InventoryAnalyticsPayload(BaseModel):
    """Top-level envelope returned by the Inventory Analytics Engine."""
    overview: InventoryOverviewMetrics
    movement: InventoryMovement
    stock_analysis: StockAnalysis
    utilization: UtilizationAnalysis
    rankings: InventoryRankings
    outliers: InventoryOutliers
    trends: InventoryTrends
    filters_applied: Dict[str, Any] = {}
    cached: bool = Field(default=False, description="Whether this result was served from cache")
