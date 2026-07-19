"""Pydantic models defining typed schemas for all transit time analytics outputs."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class TransitOverviewMetrics(BaseModel):
    """Top-level transit time KPIs across the logistics network."""
    avg_transit_time: float = Field(description="Mean transit time in days across all shipments")
    median_transit_time: float = Field(description="Median transit time in days")
    min_transit_time: float = Field(description="Fastest single shipment transit time in days")
    max_transit_time: float = Field(description="Slowest single shipment transit time in days")
    transit_variance: float = Field(description="Variance of transit times")
    transit_std_deviation: float = Field(description="Standard deviation of transit times")
    total_shipments: int = Field(description="Total number of shipments analyzed")
    avg_transit_per_route: float = Field(description="Mean transit time averaged across unique routes")
    avg_transit_per_hub: float = Field(description="Mean transit time averaged across origin hubs")
    avg_transit_per_repair_center: float = Field(description="Mean transit time averaged across repair centers")
    avg_transit_per_partner: float = Field(description="Mean transit time averaged across logistics partners")
    avg_transit_per_priority: float = Field(description="Mean transit time averaged across priority levels")
    avg_transit_per_flow_type: float = Field(description="Mean transit time averaged across flow types")


class TransitBreakdownItem(BaseModel):
    """A single row in a transit time breakdown."""
    name: str = Field(description="Entity name (route, hub, partner, etc.)")
    avg_transit_time: float = Field(description="Average transit time for this entity")
    min_transit_time: float = Field(description="Minimum transit time for this entity")
    max_transit_time: float = Field(description="Maximum transit time for this entity")
    shipment_count: int = Field(description="Number of shipments for this entity")


class TransitDistributionBucket(BaseModel):
    """A single bucket in a transit time histogram."""
    bucket_label: str = Field(description="Bucket range label (e.g., '0-1 days')")
    count: int = Field(description="Number of shipments in this bucket")
    percentage: float = Field(description="Percentage of total shipments in this bucket")


class TransitCategory(BaseModel):
    """Classification of shipments by transit speed category."""
    category: str = Field(description="Category name: Fast, Normal, Slow, Critical Delay")
    count: int = Field(description="Number of shipments in this category")
    percentage: float = Field(description="Percentage of total")
    avg_transit_time: float = Field(description="Average transit time within this category")


class TransitDistribution(BaseModel):
    """Container for transit distribution analysis."""
    histogram: List[TransitDistributionBucket] = []
    categories: List[TransitCategory] = []
    frequency: Dict[int, int] = Field(default_factory=dict, description="Mapping of transit_days -> count")


class TransitRankingEntry(BaseModel):
    """A single entry in a transit time ranking list."""
    rank: int = Field(description="Position in ranking (1-indexed)")
    entity_name: str = Field(description="Name of the ranked entity")
    avg_transit_time: float = Field(description="Average transit time used for ranking")
    shipment_count: int = Field(description="Number of shipments")


class TransitRankings(BaseModel):
    """Container for all 8 ranking lists."""
    fastest_routes: List[TransitRankingEntry] = []
    slowest_routes: List[TransitRankingEntry] = []
    fastest_hubs: List[TransitRankingEntry] = []
    slowest_hubs: List[TransitRankingEntry] = []
    fastest_repair_centers: List[TransitRankingEntry] = []
    slowest_repair_centers: List[TransitRankingEntry] = []
    fastest_partners: List[TransitRankingEntry] = []
    slowest_partners: List[TransitRankingEntry] = []


class TransitTrendPoint(BaseModel):
    """A single data point in a transit performance time-series."""
    period: str = Field(description="Period label (date, week, month, or quarter)")
    avg_transit_time: float = Field(description="Average transit time in this period")
    total_shipments: int = Field(description="Number of shipments in this period")
    on_time_pct: float = Field(description="Percentage of shipments meeting SLA in this period")


class TransitTrends(BaseModel):
    """Container for all 4 time-series trend datasets."""
    daily: List[TransitTrendPoint] = []
    weekly: List[TransitTrendPoint] = []
    monthly: List[TransitTrendPoint] = []
    quarterly: List[TransitTrendPoint] = []


class TransitOutlier(BaseModel):
    """A detected transit time outlier record."""
    transaction_id: str = Field(description="Transaction identifier")
    origin_hub: str = Field(description="Origin hub ID")
    destination_hub: str = Field(description="Destination hub ID")
    transit_days: float = Field(description="Actual transit time in days")
    outlier_type: str = Field(description="'extremely_slow', 'extremely_fast', 'abnormal', or 'long_delay'")
    deviation: float = Field(description="Number of IQR units from median")


class TransitOutliers(BaseModel):
    """Container for all outlier detection results."""
    extremely_slow: List[TransitOutlier] = []
    extremely_fast: List[TransitOutlier] = []
    abnormal: List[TransitOutlier] = []
    long_delay_candidates: List[TransitOutlier] = []
    total_outliers: int = 0


class TransitAnalyticsPayload(BaseModel):
    """Top-level envelope returned by the Transit Analytics Engine."""
    overview: TransitOverviewMetrics
    distribution: TransitDistribution
    rankings: TransitRankings
    trends: TransitTrends
    outliers: TransitOutliers
    filters_applied: Dict[str, Any] = {}
    cached: bool = Field(default=False, description="Whether this result was served from cache")
