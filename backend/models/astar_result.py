"""Pydantic models defining typed schemas for A* Pathfinding Engine results, performance, and payloads."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class AStarPathResult(BaseModel):
    """Represents the optimal route computed by the A* search algorithm."""
    source: str = Field(description="Origin Node ID")
    destination: str = Field(description="Destination Node ID")
    path_nodes: List[str] = Field(default_factory=list, description="Ordered sequence of Node IDs from source to destination")
    total_distance: float = Field(description="Optimal route distance in miles")
    total_cost: float = Field(description="Optimal route cost")
    total_transit_time: float = Field(description="Optimal route transit time in days")
    hops: int = Field(description="Total number of edge links/hops in the path")
    search_expansion_count: int = Field(description="Number of nodes expanded during A* search loop")
    visited_nodes_count: int = Field(description="Number of nodes popped from priority queue")
    explored_nodes_count: int = Field(description="Number of unique nodes inserted/discovered in queue")
    execution_time_ms: float = Field(description="Path search execution time in milliseconds")


class HeuristicMetrics(BaseModel):
    """Performance evaluation of a specific heuristic function."""
    heuristic_type: str = Field(description="Name of the heuristic class/mode evaluated")
    computation_time_ms: float = Field(description="Time spent evaluating heuristic values")
    cache_hits: int = Field(description="Number of heuristic calculations resolved via memory cache")
    average_error: float = Field(description="Average absolute heuristic value offset from actual cost")


class AStarPayload(BaseModel):
    """Top-level envelope returned by the A* Pathfinding Engine."""
    paths: Dict[str, Dict[str, AStarPathResult]] = Field(default_factory=dict, description="Optimal paths nested by source and destination keys")
    heuristics_performance: List[HeuristicMetrics] = Field(default_factory=list, description="Performance profiles for active heuristics")
    search_statistics: Dict[str, Any] = Field(default_factory=dict, description="A* engine run statistics (times, expansions)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Engine running metadata")
    filters_applied: Dict[str, Any] = {}
    cached: bool = Field(default=False, description="Whether this result was served from cache")
