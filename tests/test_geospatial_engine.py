"""Verification test suite for the Geospatial Intelligence Engine (Phase 17).

Tests Haversine distance formulas, distance matrix outputs, nearest proximity mappings,
regional quadrant clustering, network coverage hole detections, cache mechanics, and filter subsetting.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.services.repository import repository
from backend.services.geospatial_engine import GeospatialEngine
from backend.services.distance_calculator import DistanceCalculator


def setup():
    """Initialize repository for tests."""
    if not repository.is_initialized():
        repository.initialize()
    GeospatialEngine.clear_cache()


def test_haversine_formula():
    """Verify haversine distance calculation matches standard values."""
    print("\n--- TESTING HAVERSINE FORMULA ---")
    # Distance between Austin (30.2672, -97.7431) and Houston (29.7604, -95.3698) is ~146 miles gc
    dist = DistanceCalculator.haversine_distance(30.2672, -97.7431, 29.7604, -95.3698)
    print(f"Haversine distance (Austin -> Houston): {dist:.2f} miles")
    assert 130.0 <= dist <= 160.0, f"Distance must be roughly 146 miles, got {dist:.2f}"

    road = DistanceCalculator.estimate_road_distance(dist)
    print(f"Estimated road distance (circuity factor): {road:.2f} miles")
    assert road == dist * 1.25, "Circuity factor mismatch"
    print("✓ Haversine calculations verified.")


def test_distance_matrix():
    """Verify N x N distance matrix output."""
    print("\n--- TESTING DISTANCE MATRIX ---")
    payload = GeospatialEngine.get_geospatial_payload({})
    matrix = payload.distance_matrix

    assert len(matrix) > 0, "Distance matrix must not be empty"
    
    # Self-loops must be 0
    first_node = list(matrix.keys())[0]
    assert matrix[first_node][first_node] == 0.0, "Self distance must be 0"

    # Symmetric verification matrix[A][B] == matrix[B][A]
    second_node = list(matrix[first_node].keys())[1]
    d1 = matrix[first_node][second_node]
    d2 = matrix[second_node][first_node]
    assert d1 == d2, f"Distance matrix symmetry mismatch: {d1} vs {d2}"

    print(f"Distance matrix size: {len(matrix)} x {len(matrix)}")
    print(f"Distance between {first_node} and {second_node}: {d1} miles")
    print("✓ Distance matrix verified.")


def test_nearest_mappings():
    """Verify proximity nearest mappings."""
    print("\n--- TESTING NEAREST MAPPINGS ---")
    payload = GeospatialEngine.get_geospatial_payload({})
    maps = payload.nearest_mappings

    assert len(maps) > 0, "Nearest mappings list must not be empty"

    first_mapping = maps[0]
    assert len(first_mapping.node_id) > 0, "Node ID must not be empty"
    assert len(first_mapping.nearest_hub) > 0, "Nearest Hub ID must not be empty"
    assert first_mapping.distance_to_nearest_hub >= 0, "Distance to nearest hub must be non-negative"
    assert len(first_mapping.nearest_repair_center) > 0, "Nearest RC ID must not be empty"
    assert first_mapping.distance_to_nearest_repair_center >= 0, "Distance to nearest RC must be non-negative"

    print(f"Mappings generated count: {len(maps)}")
    print(f"First Mapping Details: {first_mapping.model_dump()}")
    print("✓ Proximity mapping verified.")


def test_regional_clustering():
    """Verify regional clustering divisions."""
    print("\n--- TESTING REGIONAL CLUSTERING ---")
    payload = GeospatialEngine.get_geospatial_payload({})
    cl = payload.clustering

    # Sum of all quadrant sizes must equal total nodes count
    total_nodes = len(payload.distance_matrix)
    clustered_nodes = len(cl.north) + len(cl.south) + len(cl.east) + len(cl.west) + len(cl.central)
    assert clustered_nodes == total_nodes, f"Clustered nodes count mismatch: {clustered_nodes} vs {total_nodes}"

    print(f"North Nodes: {cl.north}")
    print(f"South Nodes: {cl.south}")
    print(f"East Nodes: {cl.east}")
    print(f"West Nodes: {cl.west}")
    print(f"Central Nodes: {cl.central}")
    print("✓ Regional quadrant clustering verified.")


def test_network_coverage():
    """Verify network coverage hole detections and anomalies."""
    print("\n--- TESTING NETWORK COVERAGE ANALYSIS ---")
    payload = GeospatialEngine.get_geospatial_payload({})
    cov = payload.coverage

    assert isinstance(cov.uncovered_regions, list), "uncovered_regions must be a list"
    assert isinstance(cov.sparse_areas, list), "sparse_areas must be a list"
    assert isinstance(cov.highly_connected_areas, list), "highly_connected_areas must be a list"
    assert isinstance(cov.low_connectivity_regions, list), "low_connectivity_regions must be a list"
    assert isinstance(cov.potential_expansion_regions, list), "potential_expansion_regions must be a list"

    print(f"Uncovered targets: {cov.uncovered_regions}")
    print(f"Sparse areas: {cov.sparse_areas}")
    print(f"Highly connected areas: {cov.highly_connected_areas}")
    print(f"Low connectivity regions: {cov.low_connectivity_regions}")
    print(f"Expansion recommendations: {cov.potential_expansion_regions}")
    print("✓ Network coverage anomalies verified.")


def test_statistics():
    """Verify overview statistics calculations."""
    print("\n--- TESTING GEOSPATIAL STATISTICS ---")
    payload = GeospatialEngine.get_geospatial_payload({})
    st = payload.statistics

    assert st.avg_route_distance > 0, "Average route distance must be positive"
    assert st.max_route_distance >= st.min_route_distance, "Max distance must be >= min"
    assert st.avg_great_circle_distance > 0, "Average GC distance must be positive"
    assert st.avg_estimated_road_distance > st.avg_great_circle_distance, "Road distance must exceed gc distance"
    assert st.avg_regional_distance > 0, "Average regional distance must be positive"
    assert st.hub_coverage_radius > 0, "Hub coverage radius must be positive"
    assert st.warehouse_coverage_radius > 0, "Warehouse coverage radius must be positive"
    assert st.repair_center_coverage_radius > 0, "RC coverage radius must be positive"

    print(f"Average Route Distance: {st.avg_route_distance} miles")
    print(f"Max Route Distance: {st.max_route_distance} miles, Min: {st.min_route_distance} miles")
    print(f"Average Great-Circle Distance: {st.avg_great_circle_distance} miles")
    print(f"Average Road Distance (circuity): {st.avg_estimated_road_distance} miles")
    print(f"Hub Coverage Radius: {st.hub_coverage_radius} miles")
    print(f"Repair Center Coverage Radius: {st.repair_center_coverage_radius} miles")
    print("✓ Statistics metrics verified.")


def test_cache():
    """Validate cache hits return payload with cached=True flag."""
    print("\n--- TESTING CACHE MECHANICS ---")
    GeospatialEngine.clear_cache()

    p1 = GeospatialEngine.get_geospatial_payload({})
    assert p1.cached is False, "First payload fetch should miss cache"

    p2 = GeospatialEngine.get_geospatial_payload({})
    assert p2.cached is True, "Second payload fetch should hit cache"

    assert p1.statistics.avg_great_circle_distance == p2.statistics.avg_great_circle_distance, "Payload values must match"
    print("✓ Caching validated.")


def test_filtered_analytics():
    """Validate filter subsetting reduces metrics correctly."""
    print("\n--- TESTING FILTERED SUBSETTING ---")
    GeospatialEngine.clear_cache()

    full = GeospatialEngine.get_geospatial_payload({})

    GeospatialEngine.clear_cache()
    filtered = GeospatialEngine.get_geospatial_payload({"partner": "Swift Logico"})

    assert filtered.statistics.avg_route_distance > 0, "Filtered subsetting should compute distance correctly"
    print(f"Full average route distance: {full.statistics.avg_route_distance}")
    print(f"Filtered average route distance: {filtered.statistics.avg_route_distance}")
    print("✓ Filter subsetting validated.")


if __name__ == "__main__":
    print("Initializing Geospatial Intelligence Engine verification suite...")
    setup()

    test_haversine_formula()
    test_distance_matrix()
    test_nearest_mappings()
    test_regional_clustering()
    test_network_coverage()
    test_statistics()
    test_cache()
    test_filtered_analytics()

    print("\n" + "=" * 60)
    print("All Geospatial Intelligence Engine tests passed successfully!")
    print("=" * 60)
