"""Pydantic models defining typed schemas for all geographical intelligence outputs."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class GeospatialOverviewMetrics(BaseModel):
    """Top-level geographic KPIs across the logistics network."""
    avg_route_distance: float = Field(description="Mean transit distance in miles across all routes")
    max_route_distance: float = Field(description="Maximum route distance in miles")
    min_route_distance: float = Field(description="Minimum route distance in miles")
    avg_great_circle_distance: float = Field(description="Mean direct geographical distance across all edges")
    avg_estimated_road_distance: float = Field(description="Mean estimated road distance (great-circle * 1.25)")
    avg_regional_distance: float = Field(description="Average distance within region clusters")
    hub_coverage_radius: float = Field(description="Average coverage radius for hubs in miles")
    warehouse_coverage_radius: float = Field(description="Average coverage radius for warehouses in miles")
    repair_center_coverage_radius: float = Field(description="Average coverage radius for repair centers in miles")


class NearestMapping(BaseModel):
    """Geographic proximity mappings for a single node."""
    node_id: str = Field(description="Source Node ID")
    nearest_hub: str = Field(description="Nearest Logistics Hub ID")
    distance_to_nearest_hub: float = Field(description="Geographic distance to nearest hub in miles")
    nearest_warehouse: str = Field(description="Nearest Warehouse ID")
    distance_to_nearest_warehouse: float = Field(description="Geographic distance to nearest warehouse in miles")
    nearest_repair_center: str = Field(description="Nearest Repair Center ID")
    distance_to_nearest_repair_center: float = Field(description="Geographic distance to nearest repair center in miles")


class RegionalClustering(BaseModel):
    """Nodes grouped by geographic quadrants based on lat/lon coordinates."""
    north: List[str] = Field(default_factory=list, description="North Quadrant Node IDs")
    south: List[str] = Field(default_factory=list, description="South Quadrant Node IDs")
    east: List[str] = Field(default_factory=list, description="East Quadrant Node IDs")
    west: List[str] = Field(default_factory=list, description="West Quadrant Node IDs")
    central: List[str] = Field(default_factory=list, description="Central Quadrant Node IDs")


class NetworkCoverageMetrics(BaseModel):
    """Coverage and connectivity issues identified across regions."""
    uncovered_regions: List[str] = Field(default_factory=list, description="Operational zones lacking hub coverage")
    sparse_areas: List[str] = Field(default_factory=list, description="Node IDs with nearest neighbor distance > 300 miles")
    highly_connected_areas: List[str] = Field(default_factory=list, description="Node IDs with nearest neighbor distance < 100 miles")
    low_connectivity_regions: List[str] = Field(default_factory=list, description="Regions with low route density")
    potential_expansion_regions: List[str] = Field(default_factory=list, description="Recommended cities/zones for network expansion")


class GeospatialAnalyticsPayload(BaseModel):
    """Top-level envelope returned by the Geospatial Intelligence Engine."""
    distance_matrix: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="Great-circle distance matrix between all nodes")
    nearest_mappings: List[NearestMapping] = Field(default_factory=list)
    clustering: RegionalClustering
    statistics: GeospatialOverviewMetrics
    coverage: NetworkCoverageMetrics
    filters_applied: Dict[str, Any] = {}
    cached: bool = Field(default=False, description="Whether this result was served from cache")
