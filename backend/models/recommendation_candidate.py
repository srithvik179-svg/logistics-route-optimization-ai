"""Pydantic model representing a candidate route recommendation option with explainability factors."""

from pydantic import BaseModel, Field
from typing import List, Dict


class RecommendationCandidate(BaseModel):
    """Represents a specific routing path option prepared as a recommendation candidate."""
    candidate_id: str = Field(description="Unique candidate identifier")
    algorithm: str = Field(description="Originating search algorithm: Dijkstra, A*, GA, ACO, Balanced")
    path_nodes: List[str] = Field(description="Node sequence path array")
    distance: float = Field(description="Path distance in miles")
    cost: float = Field(description="Path shipment cost")
    transit_time: float = Field(description="Path transit duration in days")
    is_feasible: bool = Field(description="Whether the candidate satisfies all network constraints")
    composite_score: float = Field(description="Path composite score rating")
    explainability_factors: Dict[str, float] = Field(description="Relative weight values of the decision factors")
    confidence_score: float = Field(description="Algorithmic recommendation confidence index (0.0 to 1.0)")
