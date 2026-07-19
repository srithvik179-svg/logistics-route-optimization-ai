"""Pydantic models defining typed schemas for all route graph representations."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class GraphNode(BaseModel):
    """Represents a node in the logistics network graph."""
    node_id: str = Field(description="Unique node identifier (e.g. Hub ID or RC ID)")
    name: str = Field(description="Node name")
    node_type: str = Field(description="Node classification: Hub, Warehouse, Repair Center, Distribution Center")
    latitude: float = Field(description="Geographic latitude coordinate")
    longitude: float = Field(description="Geographic longitude coordinate")
    region: str = Field(description="Geographic operations region")
    city: str = Field(description="City location")
    capacity: float = Field(description="Total storage capacity limit of this node")


class GraphEdge(BaseModel):
    """Represents a directed weighted link between two nodes in the graph."""
    source: str = Field(description="Origin node ID")
    destination: str = Field(description="Destination node ID")
    distance: float = Field(description="Transit distance in miles or kilometers")
    transit_time: float = Field(description="Average transit duration in days")
    cost: float = Field(description="Average shipment transportation cost")
    volume: float = Field(description="Total cumulative shipment volume moved over this route")
    capacity: float = Field(description="Route or destination capacity limit")
    status: str = Field(description="Route operational status: Active, Congested, Disrupted")
    logistics_partner: str = Field(description="Assigned logistics partner name")


class GraphOverviewStats(BaseModel):
    """Network-level topology statistics."""
    total_nodes: int = Field(description="Total count of nodes in the graph")
    total_edges: int = Field(description="Total count of edges in the graph")
    avg_node_degree: float = Field(description="Average degree (in-degree + out-degree) per node")
    max_degree: int = Field(description="Maximum degree recorded at any single node")
    min_degree: int = Field(description="Minimum degree recorded at any single node")
    connected_components: int = Field(description="Number of isolated connected sub-networks")
    isolated_nodes: int = Field(description="Count of nodes with degree == 0")
    graph_density: float = Field(description="Ratio of actual edges to possible edges")
    avg_route_length: float = Field(description="Average edge distance across all routes")


class ConnectivityAnalysis(BaseModel):
    """Detailed topological connectivity and routing vulnerabilities analysis."""
    disconnected_networks: List[List[str]] = Field(default_factory=list, description="Subsets of node IDs that form disconnected subgraphs")
    dead_end_nodes: List[str] = Field(default_factory=list, description="Nodes with out-degree == 0 (no outgoing routes)")
    highly_connected_hubs: List[str] = Field(default_factory=list, description="Nodes with degree > average node degree + 1.5 standard deviations")
    critical_connections: List[str] = Field(default_factory=list, description="Edges with highest volumes or centrality")
    bridge_routes: List[str] = Field(default_factory=list, description="Edges whose removal increases the number of connected components")


class WeightedRouteEntry(BaseModel):
    """A weighted route representation useful for shortest path search algorithms."""
    source: str
    destination: str
    weight_distance: float
    weight_cost: float
    weight_time: float


class GraphAnalyticsPayload(BaseModel):
    """Top-level envelope returned by the Route Graph Engine."""
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    adjacency_list: Dict[str, List[str]] = Field(default_factory=dict, description="Adjacency list mapping node -> list of neighbors")
    adjacency_matrix: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="Adjacency matrix mapping source -> dest -> distance weight")
    neighbor_mapping: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict, description="Detailed neighbor mapping with weights")
    weighted_route_list: List[WeightedRouteEntry] = Field(default_factory=list)
    statistics: GraphOverviewStats
    connectivity: ConnectivityAnalysis
    filters_applied: Dict[str, Any] = {}
    cached: bool = Field(default=False, description="Whether this result was served from cache")
