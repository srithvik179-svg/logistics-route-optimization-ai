"""Pydantic models defining typed schemas for all shortest path calculations and network routing analyses."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class PathResult(BaseModel):
    """Detailed result of a single origin-destination routing path query."""
    source: str = Field(description="Origin node ID")
    destination: str = Field(description="Destination node ID")
    path_nodes: List[str] = Field(default_factory=list, description="Ordered sequence of node IDs representing the path")
    total_distance: float = Field(description="Sum of edge distances in miles")
    total_cost: float = Field(description="Sum of edge shipment costs")
    total_transit_time: float = Field(description="Sum of edge transit durations in days")
    hops: int = Field(description="Total count of edge links crossed (hops = nodes - 1)")


class ShortestPathOverviewStats(BaseModel):
    """Execution performance and structural statistics for routing calculations."""
    average_search_time_ms: float = Field(description="Mean execution duration per query in milliseconds")
    average_path_length: float = Field(description="Mean node sequence length of all valid paths")
    max_path_length: float = Field(description="Maximum path length sequence count")
    min_path_length: float = Field(description="Minimum path length sequence count")
    total_calculations: int = Field(description="Total count of shortest paths evaluated")


class NetworkAccessibility(BaseModel):
    """Vulnerability and accessibility analysis of network nodes."""
    reachable_nodes: Dict[str, List[str]] = Field(default_factory=dict, description="Source node mapping to list of reachable destinations")
    unreachable_nodes: Dict[str, List[str]] = Field(default_factory=dict, description="Source node mapping to list of unreachable destinations")
    highly_accessible_hubs: List[str] = Field(default_factory=list, description="Hubs reachable from the highest count of other nodes")
    least_accessible_hubs: List[str] = Field(default_factory=list, description="Hubs reachable from the lowest count of other nodes")


class ShortestPathPayload(BaseModel):
    """Top-level envelope returned by the Shortest Path Analytics Engine."""
    shortest_paths: Dict[str, Dict[str, PathResult]] = Field(default_factory=dict, description="Shortest paths map: source -> destination -> PathResult")
    statistics: ShortestPathOverviewStats
    accessibility: NetworkAccessibility
    filters_applied: Dict[str, Any] = {}
    cached: bool = Field(default=False, description="Whether this result was served from cache")
