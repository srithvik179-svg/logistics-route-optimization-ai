"""Pydantic models defining typed schemas for all SLA analytics outputs."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class SLAOverviewMetrics(BaseModel):
    """Top-level SLA compliance KPIs across the network."""
    overall_compliance_pct: float = Field(description="Percentage of total transactions meeting SLA")
    total_shipments: int = Field(description="Total shipments evaluated")
    sla_met_count: int = Field(description="Number of shipments that met SLA")
    sla_violations: int = Field(description="Number of shipments that missed SLA")
    avg_delay_beyond_sla: float = Field(description="Average delay in days beyond SLA limit for violated shipments")
    avg_early_completion: float = Field(description="Average days completed early for compliant shipments")
    sla_success_rate: float = Field(description="Success rate percentage (same as compliance)")


class SLADimensionItem(BaseModel):
    """Detailed SLA compliance numbers for a specific entity."""
    name: str = Field(description="Entity identifier (Hub ID, RC ID, Route key, etc.)")
    compliance_pct: float = Field(description="Compliance rate percentage")
    total_count: int = Field(description="Total shipments processed")
    violations: int = Field(description="SLA missed count")


class SLADimensionalBreakdowns(BaseModel):
    """SLA compliance breakdowns grouped by various dimensions."""
    by_hub: List[SLADimensionItem] = Field(default_factory=list)
    by_repair_center: List[SLADimensionItem] = Field(default_factory=list)
    by_partner: List[SLADimensionItem] = Field(default_factory=list)
    by_route: List[SLADimensionItem] = Field(default_factory=list)
    by_region: List[SLADimensionItem] = Field(default_factory=list)
    by_priority: List[SLADimensionItem] = Field(default_factory=list)
    by_category: List[SLADimensionItem] = Field(default_factory=list)


class ViolationEntity(BaseModel):
    """Details about a violated or delayed entity/part."""
    name: str = Field(description="Identifier of the entity, route or part")
    violation_count: int = Field(description="Total SLA violations count")
    avg_delay_days: float = Field(description="Average delay beyond SLA threshold in days")
    risk_level: str = Field(description="Risk classification: Critical, High, Medium, Low")


class SLAOutliersAndViolations(BaseModel):
    """Container for critical delays and repeated violations analyses."""
    high_delay_routes: List[ViolationEntity] = Field(default_factory=list)
    repeated_sla_violations: List[ViolationEntity] = Field(default_factory=list)
    critical_delay_locations: List[ViolationEntity] = Field(default_factory=list)
    critical_logistics_partners: List[ViolationEntity] = Field(default_factory=list)
    frequently_delayed_parts: List[ViolationEntity] = Field(default_factory=list)
    total_violations_recorded: int = Field(0, description="Overall total violations count")


class SLARankingEntry(BaseModel):
    """SLA ranking entry."""
    rank: int = Field(description="Position in ranking (1-indexed)")
    entity_name: str = Field(description="Name of the ranked entity")
    compliance_pct: float = Field(description="SLA compliance rate percentage")
    total_shipments: int = Field(description="Total shipments handled")


class SLARankings(BaseModel):
    """SLA performance rankings."""
    best_performing_hubs: List[SLARankingEntry] = Field(default_factory=list)
    worst_performing_hubs: List[SLARankingEntry] = Field(default_factory=list)
    best_logistics_partners: List[SLARankingEntry] = Field(default_factory=list)
    worst_logistics_partners: List[SLARankingEntry] = Field(default_factory=list)
    best_repair_centers: List[SLARankingEntry] = Field(default_factory=list)
    worst_repair_centers: List[SLARankingEntry] = Field(default_factory=list)
    most_reliable_routes: List[SLARankingEntry] = Field(default_factory=list)
    least_reliable_routes: List[SLARankingEntry] = Field(default_factory=list)


class SLATrendPoint(BaseModel):
    """SLA compliance metric over a timeframe."""
    period: str = Field(description="Period label (date, week, month, or quarter)")
    compliance_pct: float = Field(description="SLA compliance rate percentage")
    total_shipments: int = Field(description="Number of shipments in this period")
    violation_count: int = Field(description="Number of SLA violations in this period")


class SLATrends(BaseModel):
    """Chronological SLA trends."""
    daily: List[SLATrendPoint] = Field(default_factory=list)
    weekly: List[SLATrendPoint] = Field(default_factory=list)
    monthly: List[SLATrendPoint] = Field(default_factory=list)
    quarterly: List[SLATrendPoint] = Field(default_factory=list)


class SLAAnalyticsPayload(BaseModel):
    """Top-level envelope returned by the SLA Analytics Engine."""
    overview: SLAOverviewMetrics
    breakdowns: SLADimensionalBreakdowns
    violations_analysis: SLAOutliersAndViolations
    rankings: SLARankings
    trends: SLATrends
    filters_applied: Dict[str, Any] = {}
    cached: bool = Field(default=False, description="Whether this result was served from cache")
