"""Pydantic models representing population states and generational evolution metrics."""

from pydantic import BaseModel, Field
from typing import List
from backend.models.chromosome import Chromosome


class GenerationStats(BaseModel):
    """Statistics summarizing the fitness levels of a specific generation."""
    generation_index: int = Field(description="Generation counter index")
    best_fitness: float = Field(description="Highest fitness value recorded")
    average_fitness: float = Field(description="Average fitness value across population")
    worst_fitness: float = Field(description="Lowest fitness value recorded")
    diversity: float = Field(description="Proportion of unique route paths in population (0.0 to 1.0)")


class Population(BaseModel):
    """Represents a full set of candidate chromosomes in the active generation."""
    chromosomes: List[Chromosome] = Field(default_factory=list, description="Active candidate solutions")
    generation_index: int = Field(description="Active generation number")
    stats: GenerationStats
