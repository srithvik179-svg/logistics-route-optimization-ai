"""Pydantic model representing the pheromone matrix mapping."""

from pydantic import BaseModel, Field
from typing import Dict


class PheromoneMatrix(BaseModel):
    """Stores the levels of pheromones deposited across the logistics network graph edges."""
    matrix: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="Pheromone mapping source -> destination -> pheromone level")
