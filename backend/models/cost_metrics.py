"""Pydantic models defining typed schemas for all cost analytics outputs."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class CostOverviewMetrics(BaseModel):
    """Top-level cost KPIs across the logistics network."""
    overall_logistics_cost: float = Field(description="Sum of all shipment costs")
    avg_shipment_cost: float = Field(description="Mean cost per shipment")
    avg_route_cost: float = Field(description="Mean cost per unique route")
    avg_cost_per_hub: float = Field(description="Mean cost per hub")
    avg_cost_per_repair_center: float = Field(description="Mean cost per repair center")
    avg_cost_per_partner: float = Field(description="Mean cost per logistics partner")
    avg_cost_per_category: float = Field(description="Mean cost per part category")
    avg_cost_per_flow_type: float = Field(description="Mean cost per flow type")
    total_shipments: int = Field(description="Total number of shipments analyzed")


class CostBreakdownItem(BaseModel):
    """A single row in a cost breakdown analysis."""
    name: str = Field(description="Entity name (hub ID, route key, partner name, etc.)")
    total_cost: float = Field(description="Aggregate cost for this entity")
    avg_cost: float = Field(description="Average cost per shipment for this entity")
    shipment_count: int = Field(description="Number of shipments attributed to this entity")


class CostVarianceMetrics(BaseModel):
    """Descriptive statistics for shipment cost distribution."""
    maximum: float = Field(description="Highest single shipment cost")
    minimum: float = Field(description="Lowest single shipment cost")
    median: float = Field(description="Median shipment cost")
    std_deviation: float = Field(description="Standard deviation of shipment costs")
    variance: float = Field(description="Variance of shipment costs")
    q1: float = Field(description="First quartile (25th percentile)")
    q3: float = Field(description="Third quartile (75th percentile)")
    iqr: float = Field(description="Interquartile range (Q3 - Q1)")


class CostRankingEntry(BaseModel):
    """A single entry in a cost ranking list."""
    rank: int = Field(description="Position in ranking (1-indexed)")
    entity_name: str = Field(description="Name of the ranked entity")
    metric_value: float = Field(description="Cost metric used for ranking")


class CostTrendPoint(BaseModel):
    """A single data point in a cost time-series."""
    period: str = Field(description="Period label (date, week, month, or quarter)")
    total_cost: float = Field(description="Aggregate cost in this period")
    avg_cost: float = Field(description="Average cost per shipment in this period")
    shipment_count: int = Field(description="Number of shipments in this period")


class CostBreakdowns(BaseModel):
    """Container for all 8 breakdown dimensions."""
    by_hub: List[CostBreakdownItem] = []
    by_route: List[CostBreakdownItem] = []
    by_repair_center: List[CostBreakdownItem] = []
    by_partner: List[CostBreakdownItem] = []
    by_region: List[CostBreakdownItem] = []
    by_priority: List[CostBreakdownItem] = []
    by_category: List[CostBreakdownItem] = []
    by_status: List[CostBreakdownItem] = []


class CostRankings(BaseModel):
    """Container for all 6 ranking lists."""
    top_expensive_routes: List[CostRankingEntry] = []
    lowest_cost_routes: List[CostRankingEntry] = []
    highest_cost_partners: List[CostRankingEntry] = []
    lowest_cost_partners: List[CostRankingEntry] = []
    highest_cost_hubs: List[CostRankingEntry] = []
    lowest_cost_hubs: List[CostRankingEntry] = []


class CostTrends(BaseModel):
    """Container for all 4 time-series trend datasets."""
    daily: List[CostTrendPoint] = []
    weekly: List[CostTrendPoint] = []
    monthly: List[CostTrendPoint] = []
    quarterly: List[CostTrendPoint] = []


class CostAnalyticsPayload(BaseModel):
    """Top-level envelope returned by the Cost Analytics Engine."""
    overview: CostOverviewMetrics
    breakdowns: CostBreakdowns
    variance: CostVarianceMetrics
    rankings: CostRankings
    trends: CostTrends
    filters_applied: Dict[str, Any] = {}
    cached: bool = Field(default=False, description="Whether this result was served from cache")
