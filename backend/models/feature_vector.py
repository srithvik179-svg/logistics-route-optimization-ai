"""Pydantic model representing standardized feature vectors for logistics route paths."""

from pydantic import BaseModel, Field


class FeatureVector(BaseModel):
    """Represents a standardized, normalized feature vector of a candidate path."""
    cost: float = Field(description="Normalized cost index (lower is better, e.g. 0.0 to 1.0)")
    transit_time: float = Field(description="Normalized transit duration index (0.0 to 1.0)")
    distance: float = Field(description="Total path distance in miles")
    capacity_utilization: float = Field(description="Remaining link capacity fraction (0.0 to 1.0)")
    sla_compliance: float = Field(description="Estimated SLA compliance probability (0.0 to 1.0)")
    reliability: float = Field(description="Historical route reliability coefficient (0.0 to 1.0)")
    partner_performance: float = Field(description="Average transport partner score (0.0 to 1.0)")
    operational_efficiency: float = Field(description="Composite operational efficiency rating")
    composite_score: float = Field(description="Global composite score of the route (0.0 to 100.0)")
