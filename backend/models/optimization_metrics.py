"""Pydantic models defining typed schemas for optimization preprocessing, constraints, matrices, and payloads."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class OptimizationNode(BaseModel):
    """Represents a node formatted for matrix indexing in pathfinding/optimization algorithms."""
    node_id: str = Field(description="Unique Node ID")
    matrix_index: int = Field(description="Integer index for matrix lookup rows and columns")
    node_type: str = Field(description="Node type: Hub, Warehouse, Repair Center")
    capacity: float = Field(description="Max capacity limit")
    normalized_score: float = Field(description="Normalized capacity/availability score (0.0 to 1.0)")


class OptimizationEdge(BaseModel):
    """Represents a graph edge preprocessed for optimization algorithms."""
    source: str = Field(description="Origin Node ID")
    destination: str = Field(description="Destination Node ID")
    source_index: int = Field(description="Integer index of origin node")
    destination_index: int = Field(description="Integer index of destination node")
    distance: float = Field(description="Travel distance in miles")
    cost: float = Field(description="Transportation cost")
    transit_time: float = Field(description="Transit duration in days")
    capacity: float = Field(description="Capacity limit")
    volume: float = Field(description="Cumulative flow volume")
    status: str = Field(description="Route operational status")
    normalized_weight: float = Field(description="Normalized cost/distance weight (0.0 to 1.0) used by search loops")


class OptimizationConstraints(BaseModel):
    """Network-wide threshold limits enforced during optimization path search."""
    max_distance_limit: float = Field(description="Maximum allowed route distance in miles")
    max_cost_limit: float = Field(description="Maximum allowed shipment cost")
    max_transit_time_limit: float = Field(description="Maximum allowed transit time in days")
    min_sla_target_compliance: float = Field(description="Minimum acceptable SLA target compliance %")


class NetworkBaselines(BaseModel):
    """Average metrics representing the baseline network state before optimization."""
    baseline_cost: float = Field(description="Average route transport cost")
    baseline_transit_time: float = Field(description="Average route transit time in days")
    baseline_capacity_utilization: float = Field(description="Average capacity utilization fraction (0.0 to 1.0)")
    baseline_sla_compliance: float = Field(description="Average route SLA compliance %")
    baseline_operational_efficiency: float = Field(description="Average overall route operational efficiency (0.0 to 100.0)")
    baseline_route_performance: float = Field(description="Average route performance index")


class GraphValidationResult(BaseModel):
    """Network topology integrity report verifying graph consistency."""
    has_warnings: bool = Field(description="Whether any warning alerts were recorded")
    is_valid: bool = Field(description="Whether the graph structure is clean for optimization algorithms")
    warnings: List[str] = Field(default_factory=list, description="Descriptive list of warnings (missing nodes, disconnected parts)")
    disconnected_components_count: int = Field(description="Total connected components found")
    has_negative_weights: bool = Field(description="Whether any edge has negative cost/distance values")
    has_duplicate_edges: bool = Field(description="Whether any parallel edges exist")


class OptimizationReadinessPayload(BaseModel):
    """Top-level envelope returned by the Network Optimization Readiness Engine."""
    nodes: List[OptimizationNode] = Field(default_factory=list)
    edges: List[OptimizationEdge] = Field(default_factory=list)
    distance_matrix: List[List[float]] = Field(default_factory=list, description="Distance matrix indexed by node integer indexes")
    cost_matrix: List[List[float]] = Field(default_factory=list, description="Cost matrix indexed by node integer indexes")
    transit_matrix: List[List[float]] = Field(default_factory=list, description="Transit time matrix indexed by node integer indexes")
    capacity_matrix: List[List[float]] = Field(default_factory=list, description="Capacity matrix indexed by node integer indexes")
    sla_matrix: List[List[float]] = Field(default_factory=list, description="SLA matrix indexed by node integer indexes")
    constraints: OptimizationConstraints
    baselines: NetworkBaselines
    validation: GraphValidationResult
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Optimization settings and statistics")
    filters_applied: Dict[str, Any] = {}
    cached: bool = Field(default=False, description="Whether this result was served from cache")
