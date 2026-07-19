"""Pydantic model representing an artificial ant state during route construction."""

from pydantic import BaseModel, Field
from typing import List


class Ant(BaseModel):
    """Represents a single artificial ant and its constructed route path metrics."""
    path_nodes: List[str] = Field(default_factory=list, description="Sequence of Node IDs traversed by the ant")
    distance: float = Field(description="Total path distance in miles")
    cost: float = Field(description="Total transportation cost")
    transit_time: float = Field(description="Total transit duration in days")
    is_feasible: bool = Field(description="Whether the route satisfies all network constraints")
    fitness: float = Field(description="Scoring utility of the path (higher is better)")
