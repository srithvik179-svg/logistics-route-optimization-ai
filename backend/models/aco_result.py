"""Pydantic models representing Ant Colony Optimization statistics, benchmarks, and payloads."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any
from backend.models.ant import Ant
from backend.models.pheromone_matrix import PheromoneMatrix


class ACOIterationStats(BaseModel):
    """Generational statistics compiled after each ACO ant swarm construction loop."""
    iteration_index: int = Field(description="Iteration counter index")
    best_fitness: float = Field(description="Highest path fitness recorded in this iteration")
    average_fitness: float = Field(description="Average path fitness across the swarm")
    worst_fitness: float = Field(description="Lowest path fitness recorded in this iteration")
    paths_found_count: int = Field(description="Total count of ants that successfully reached the destination")


class BenchmarkEntry(BaseModel):
    """Performance profile comparing search algorithms on the same route request."""
    algorithm: str = Field(description="Name of the routing algorithm evaluated")
    distance: float = Field(description="Total path distance in miles")
    cost: float = Field(description="Total transportation cost")
    transit_time: float = Field(description="Total transit duration in days")
    hops: int = Field(description="Total number of edge links/hops")
    execution_time_ms: float = Field(description="Calculation run duration in milliseconds")
    quality_score: float = Field(description="Overall path quality index (0.0 to 100.0)")


class ACOPayload(BaseModel):
    """Top-level response envelope returned by the Ant Colony Optimization Engine."""
    optimized_route: Ant = Field(description="Best path solution discovered by the ant colony")
    iteration_history: List[ACOIterationStats] = Field(default_factory=list, description="Generational iteration swarm statistics history")
    pheromone_matrix: PheromoneMatrix = Field(description="Final updated pheromone level matrix")
    benchmarks: List[BenchmarkEntry] = Field(default_factory=list, description="Benchmarking results comparison dataset")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Swarm settings and performance parameters")
    filters_applied: Dict[str, Any] = {}
    cached: bool = Field(default=False, description="Whether this result was served from cache")
