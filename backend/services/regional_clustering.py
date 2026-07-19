"""Geographic quadrant regional clustering for logistics network nodes."""

from typing import List, Dict, Tuple
import numpy as np

from backend.models.geospatial_metrics import RegionalClustering
from backend.utils.logger import logger


class RegionalClusteringService:
    """Classifies geographic locations into North, South, East, West, and Central quadrants.

    Stateless service designed for dependency injection.
    """

    @classmethod
    def perform_clustering(cls, node_coords: Dict[str, Tuple[float, float]]) -> RegionalClustering:
        """Clusters nodes based on latitude and longitude quadrant offsets relative to center.

        Args:
            node_coords: Dictionary mapping node_id to (lat, lon) coordinates tuple.

        Returns:
            RegionalClustering: Populated quadrant groupings.
        """
        logger.info("RegionalClusteringService: Performing regional clustering.")

        clustering = RegionalClustering()
        if not node_coords:
            return clustering

        lats = [c[0] for c in node_coords.values()]
        lons = [c[1] for c in node_coords.values()]

        # Compute center point of the active network
        mean_lat = float(np.mean(lats))
        mean_lon = float(np.mean(lons))

        # Standard deviation offsets to define "Central" boundary
        std_lat = float(np.std(lats)) if len(lats) > 1 else 0.5
        std_lon = float(np.std(lons)) if len(lons) > 1 else 0.5
        
        lat_offset = std_lat * 0.4
        lon_offset = std_lon * 0.4

        for node_id, coords in node_coords.items():
            lat, lon = coords[0], coords[1]

            # Central Quadrant Check
            if (mean_lat - lat_offset <= lat <= mean_lat + lat_offset) and \
               (mean_lon - lon_offset <= lon <= mean_lon + lon_offset):
                clustering.central.append(node_id)
            elif lat > mean_lat + lat_offset:
                # North
                if lon > mean_lon + lon_offset:
                    clustering.east.append(node_id)  # North-East falls to East
                else:
                    clustering.north.append(node_id)
            elif lat < mean_lat - lat_offset:
                # South
                if lon < mean_lon - lon_offset:
                    clustering.west.append(node_id)  # South-West falls to West
                else:
                    clustering.south.append(node_id)
            elif lon > mean_lon + lon_offset:
                clustering.east.append(node_id)
            else:
                clustering.west.append(node_id)

        # Fallback empty protections: if any quadrant is completely empty, it is fine
        logger.info("RegionalClusteringService: Regional Clustering Completed.")
        return clustering
