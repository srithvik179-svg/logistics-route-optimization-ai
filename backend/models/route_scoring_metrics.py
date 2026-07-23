"""Pydantic models defining typed schemas for route scoring metrics, rankings, comparisons, and payloads."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class RouteScoreResult(BaseModel):
    """Detailed score report for a specific logistics route."""
    route_id: str = Field(description="Format: Source Hub → Destination Hub")
    source: str = Field(description="Origin Node ID")
    destination: str = Field(description="Destination Node ID")
    cost_score: float = Field(description="Cost efficiency score (0 to 100)")
    transit_time_score: float = Field(description="Transit duration efficiency score (0 to 100)")
    capacity_score: float = Field(description="Optimal capacity utilization score (0 to 100)")
    sla_score: float = Field(description="Historical SLA compliance score (0 to 100)")
    distance_score: float = Field(description="Geographic distance score (0 to 100)")
    partner_reliability_score: float = Field(description="Logistics partner rating score (0 to 100)")
    overall_route_score: float = Field(description="Composite score based on weighted factors (0 to 100)")
    business_priority_score: float = Field(description="Priority rating based on demand priority factors (0 to 100)")
    operational_risk_score: float = Field(description="Risk rating combining delays and capacity overflow (0 to 100)")
    performance_index: float = Field(description="Operational speed and quality index (0 to 100)")
    composite_logistics_score: float = Field(description="Overall scoring index used by path optimization algorithms (0 to 100)")
    avg_cost: float = Field(default=0.0, description="Average cost per shipment in USD")
    total_cost: float = Field(default=0.0, description="Total cost of shipments in USD")
    sla_compliance: float = Field(default=0.0, description="Actual historical SLA compliance percentage (0 to 100)")


class RouteRankingsSet(BaseModel):
    """Rankings lists for different business prioritization strategies."""
    best_routes: List[str] = Field(default_factory=list, description="Top overall scoring route IDs")
    lowest_cost: List[str] = Field(default_factory=list, description="Top lowest cost route IDs")
    fastest: List[str] = Field(default_factory=list, description="Top fastest route IDs")
    most_reliable: List[str] = Field(default_factory=list, description="Top SLA compliant route IDs")
    highest_capacity: List[str] = Field(default_factory=list, description="Top highest capacity utilization route IDs")
    highest_performing: List[str] = Field(default_factory=list, description="Top high performing index route IDs")
    worst_performing: List[str] = Field(default_factory=list, description="Worst performing route IDs")


class ComparisonPair(BaseModel):
    """Correlation and comparison details between two routing strategies."""
    metric_a_name: str
    metric_b_name: str
    shared_routes_count: int
    correlation_coefficient: float = Field(description="Correlation coefficient (-1.0 to 1.0) between the two metrics")
    differences_summary: str = Field(description="Brief text summary explaining the trade-off")


class RouteScoringPayload(BaseModel):
    """Top-level envelope returned by the Route Cost & Scoring Engine."""
    route_scores: List[RouteScoreResult] = Field(default_factory=list)
    rankings: RouteRankingsSet
    comparisons: Dict[str, ComparisonPair] = Field(default_factory=dict)
    statistics: Dict[str, float] = Field(default_factory=dict)
    business_insights: Dict[str, List[str]] = Field(default_factory=dict)
    filters_applied: Dict[str, Any] = {}
    cached: bool = Field(default=False, description="Whether this result was served from cache")
