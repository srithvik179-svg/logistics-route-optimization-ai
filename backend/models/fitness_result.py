"""Pydantic model representing the final Genetic Algorithm optimization payload response."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from backend.models.chromosome import Chromosome
from backend.models.population import GenerationStats


class GeneticOptimizationPayload(BaseModel):
    """Top-level response envelope returned by the Genetic Algorithm Optimization Engine."""
    optimized_route: Chromosome = Field(description="Best feasible solution candidate discovered")
    fitness_history: List[float] = Field(default_factory=list, description="Sequence of best fitness scores over generations")
    generation_history: List[GenerationStats] = Field(default_factory=list, description="Topological summary stats per generation")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Evolution running metrics")
    filters_applied: Dict[str, Any] = {}
    cached: bool = Field(default=False, description="Whether this result was served from cache")
