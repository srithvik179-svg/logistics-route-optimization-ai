"""Pydantic model representing a candidate route chromosome in Genetic Algorithm loops."""

from pydantic import BaseModel, Field
from typing import List


class Chromosome(BaseModel):
    """Represents a single candidate route path candidate and its fitness scoring attributes."""
    path_nodes: List[str] = Field(description="Sequence of Node IDs composing the route")
    fitness: float = Field(description="Fitness score (higher is better)")
    is_feasible: bool = Field(description="Whether the route respects all network constraints")
    distance: float = Field(description="Total path distance in miles")
    cost: float = Field(description="Total transportation cost")
    transit_time: float = Field(description="Total transit duration in days")
    capacity_utilization: float = Field(description="Average capacity utilization fraction")
    sla_compliance: float = Field(description="Average SLA compliance index")
    reliability_score: float = Field(description="Composite reliability score (0.0 to 100.0)")
    operational_efficiency: float = Field(description="Operational efficiency score (0.0 to 100.0)")
