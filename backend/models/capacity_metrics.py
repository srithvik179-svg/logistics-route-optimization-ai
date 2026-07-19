"""Pydantic models defining typed schemas for all network capacity analytics outputs."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class CapacityOverviewMetrics(BaseModel):
    """Top-level capacity KPIs across the logistics network."""
    overall_network_capacity: float = Field(description="Sum of all storage capacity limits across all nodes")
    avg_hub_capacity: float = Field(description="Average storage capacity of hubs")
    avg_repair_center_capacity: float = Field(description="Average storage capacity of repair centers")
    available_capacity: float = Field(description="Total remaining available capacity in the network")
    used_capacity: float = Field(description="Total utilized capacity in the network")
    capacity_utilization_pct: float = Field(description="Overall utilization rate percentage")
    capacity_growth: float = Field(description="Growth rate of capacity since baseline")
    capacity_availability: float = Field(description="Capacity availability rate (available / total)")


class NodeCapacityMetrics(BaseModel):
    """Detailed capacity KPIs for a single node (Hub or Repair Center)."""
    node_id: str = Field(description="Hub or Repair Center ID")
    capacity: float = Field(description="Total capacity of this node")
    used_capacity: float = Field(description="Utilized capacity at this node")
    utilization_pct: float = Field(description="Capacity utilization rate percentage")
    remaining_capacity: float = Field(description="Remaining available capacity units")
    workload: int = Field(description="Total active transactions processed or handled")
    shipment_density: float = Field(description="Shipment density value (shipments handled per capacity unit)")
    inventory_density: float = Field(description="Inventory density value (inventory stored per capacity unit)")
    throughput: float = Field(description="Throughput volume (incoming + outgoing processed quantities)")


class RegionalCapacityDimension(BaseModel):
    """Capacity utilization details for a regional breakdown dimension."""
    capacity: float = Field(description="Total capacity in this dimension")
    used: float = Field(description="Used capacity in this dimension")
    utilization_pct: float = Field(description="Utilization rate percentage")


class RegionalCapacityBreakdown(BaseModel):
    """Capacity breakdowns aggregated across various dimensions."""
    by_region: Dict[str, RegionalCapacityDimension] = Field(default_factory=dict, description="Capacity by region")
    by_city: Dict[str, RegionalCapacityDimension] = Field(default_factory=dict, description="Capacity by city")
    by_hub_type: Dict[str, RegionalCapacityDimension] = Field(default_factory=dict, description="Capacity by hub type")
    by_flow_type: Dict[str, RegionalCapacityDimension] = Field(default_factory=dict, description="Capacity by flow type")
    by_logistics_partner: Dict[str, RegionalCapacityDimension] = Field(default_factory=dict, description="Capacity by logistics partner")


class CapacityRankingEntry(BaseModel):
    """A single entry in a capacity ranking list."""
    rank: int = Field(description="Position in ranking (1-indexed)")
    entity_name: str = Field(description="Name of the ranked entity")
    metric_value: float = Field(description="Sorting value (utilization % or capacity units)")
    capacity: float = Field(description="Total capacity of the entity")


class CapacityRankings(BaseModel):
    """Container for capacity rankings."""
    top_utilized_hubs: List[CapacityRankingEntry] = Field(default_factory=list)
    least_utilized_hubs: List[CapacityRankingEntry] = Field(default_factory=list)
    top_utilized_repair_centers: List[CapacityRankingEntry] = Field(default_factory=list)
    least_utilized_repair_centers: List[CapacityRankingEntry] = Field(default_factory=list)
    highest_capacity_regions: List[CapacityRankingEntry] = Field(default_factory=list)
    lowest_capacity_regions: List[CapacityRankingEntry] = Field(default_factory=list)


class BottleneckAnomaly(BaseModel):
    """A single detected capacity bottleneck."""
    entity_id: str = Field(description="Node ID or Region name")
    utilization_pct: float = Field(description="Utilization level at this bottleneck")
    anomaly_type: str = Field(description="'overloaded_hub', 'underutilized_hub', 'overloaded_rc', 'idle_rc', 'saturation', or 'imbalance'")
    description: str = Field(description="Explanation of the bottleneck trigger")


class CapacityBottlenecks(BaseModel):
    """Container for all detected bottlenecks and capacity saturation issues."""
    overloaded_hubs: List[BottleneckAnomaly] = Field(default_factory=list, description="Hubs with utilization > 90%")
    underutilized_hubs: List[BottleneckAnomaly] = Field(default_factory=list, description="Hubs with utilization < 20%")
    overloaded_repair_centers: List[BottleneckAnomaly] = Field(default_factory=list, description="RCs with utilization > 90%")
    idle_repair_centers: List[BottleneckAnomaly] = Field(default_factory=list, description="RCs with utilization < 15%")
    capacity_saturation_flag: bool = Field(False, description="True if overall network occupancy/utilization > 85%")
    capacity_imbalance_flag: bool = Field(False, description="True if standard deviation of utilization across nodes > 25%")
    total_bottlenecks: int = Field(0, description="Total count of anomalies detected")


class CapacityTrendPoint(BaseModel):
    """A single trend point representing capacity metrics over a timeframe."""
    period: str = Field(description="Period label (date, week, month, or quarter)")
    total_capacity: float = Field(description="Overall network capacity")
    used_capacity: float = Field(description="Used capacity in this period")
    availability_rate: float = Field(description="Available capacity rate percentage")


class CapacityTrends(BaseModel):
    """Container for capacity trends over time."""
    daily: List[CapacityTrendPoint] = Field(default_factory=list)
    weekly: List[CapacityTrendPoint] = Field(default_factory=list)
    monthly: List[CapacityTrendPoint] = Field(default_factory=list)
    quarterly: List[CapacityTrendPoint] = Field(default_factory=list)


class CapacityAnalyticsPayload(BaseModel):
    """Top-level envelope returned by the Network Capacity Analytics Engine."""
    overview: CapacityOverviewMetrics
    hubs_analysis: List[NodeCapacityMetrics] = Field(default_factory=list)
    repair_centers_analysis: List[NodeCapacityMetrics] = Field(default_factory=list)
    regional_analysis: RegionalCapacityBreakdown
    bottlenecks: CapacityBottlenecks
    rankings: CapacityRankings
    trends: CapacityTrends
    filters_applied: Dict[str, Any] = {}
    cached: bool = Field(default=False, description="Whether this result was served from cache")
