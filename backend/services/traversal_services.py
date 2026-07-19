"""Breadth-First Search (BFS) and Depth-First Search (DFS) traversal services."""

from typing import Dict, List, Any, Set, Optional, Tuple
from backend.models.shortest_path_metrics import PathResult
from backend.utils.logger import logger


class TraversalService:
    """Implements graph traversal algorithms (BFS/DFS) and accessibility calculations.

    Stateless service designed for dependency injection.
    """

    @classmethod
    def find_path_bfs(
        cls,
        neighbor_map: Dict[str, List[Dict[str, Any]]],
        source: str,
        destination: str
    ) -> Optional[PathResult]:
        """Calculates minimum hop path sequence using Breadth-First Search (BFS).

        Args:
            neighbor_map: Neighbor maps registry.
            source: Source node ID.
            destination: Destination node ID.

        Returns:
            Optional[PathResult]: Shortest hop path, else None.
        """
        if source not in neighbor_map or destination not in neighbor_map:
            return None

        # Queue stores: (node_id, path_sequence, accum_dist, accum_cost, accum_time)
        queue = [(source, [source], 0.0, 0.0, 0.0)]
        visited: Set[str] = {source}

        while queue:
            curr_node, path, dist, cost, time = queue.pop(0)

            if curr_node == destination:
                return PathResult(
                    source=source,
                    destination=destination,
                    path_nodes=path,
                    total_distance=round(dist, 2),
                    total_cost=round(cost, 2),
                    total_transit_time=round(time, 2),
                    hops=len(path) - 1
                )

            for edge in neighbor_map.get(curr_node, []):
                neigh = edge["destination"]
                if neigh not in visited:
                    visited.add(neigh)
                    queue.append((
                        neigh,
                        path + [neigh],
                        dist + edge.get("distance", 0.0),
                        cost + edge.get("cost", 0.0),
                        time + edge.get("transit_time", 0.0)
                    ))

        return None

    @classmethod
    def find_path_dfs(
        cls,
        neighbor_map: Dict[str, List[Dict[str, Any]]],
        source: str,
        destination: str
    ) -> Optional[PathResult]:
        """Calculates a valid traversal path using Depth-First Search (DFS).

        Args:
            neighbor_map: Neighbor maps registry.
            source: Source node ID.
            destination: Destination node ID.

        Returns:
            Optional[PathResult]: Traversal path, else None.
        """
        if source not in neighbor_map or destination not in neighbor_map:
            return None

        # Stack stores: (node_id, path_sequence, accum_dist, accum_cost, accum_time)
        stack = [(source, [source], 0.0, 0.0, 0.0)]
        visited: Set[str] = set()

        while stack:
            curr_node, path, dist, cost, time = stack.pop()

            if curr_node == destination:
                return PathResult(
                    source=source,
                    destination=destination,
                    path_nodes=path,
                    total_distance=round(dist, 2),
                    total_cost=round(cost, 2),
                    total_transit_time=round(time, 2),
                    hops=len(path) - 1
                )

            if curr_node not in visited:
                visited.add(curr_node)
                # Reverse neighbor order to explore in typical order
                for edge in reversed(neighbor_map.get(curr_node, [])):
                    neigh = edge["destination"]
                    if neigh not in visited:
                        stack.append((
                            neigh,
                            path + [neigh],
                            dist + edge.get("distance", 0.0),
                            cost + edge.get("cost", 0.0),
                            time + edge.get("transit_time", 0.0)
                        ))

        return None

    @classmethod
    def compute_accessibility(
        cls,
        nodes: List[str],
        neighbor_map: Dict[str, List[Dict[str, Any]]]
    ) -> Tuple[Dict[str, List[str]], Dict[str, List[str]], List[str], List[str]]:
        """Determines reachable and unreachable nodes lists for all node pairs in the graph.

        Args:
            nodes: List of all node IDs.
            neighbor_map: Neighbors registry.

        Returns:
            Tuple[reachable, unreachable, highly_accessible_hubs, least_accessible_hubs]
        """
        from collections import defaultdict

        reachable: Dict[str, List[str]] = {}
        unreachable: Dict[str, List[str]] = {}
        inbound_reach_counts = defaultdict(int)

        for src in nodes:
            # Discover all reachable nodes using standard BFS search
            visited: Set[str] = {src}
            queue = [src]

            while queue:
                curr = queue.pop(0)
                for edge in neighbor_map.get(curr, []):
                    neigh = edge["destination"]
                    if neigh not in visited:
                        visited.add(neigh)
                        queue.append(neigh)

            # Exclude self from reachable targets list
            reachable_list = sorted([n for n in visited if n != src])
            reachable[src] = reachable_list

            unreachable_list = sorted([n for n in nodes if n != src and n not in visited])
            unreachable[src] = unreachable_list

            # Count inbound reachability for accessibility ranking
            for r in reachable_list:
                inbound_reach_counts[r] += 1

        # Sort hubs by inbound accessibility counts
        hubs = [n for n in nodes if not n.startswith("TPR")]
        sorted_hubs = sorted(hubs, key=lambda x: inbound_reach_counts[x], reverse=True)

        highly_accessible = sorted_hubs[:3] if len(sorted_hubs) >= 3 else sorted_hubs
        least_accessible = sorted_hubs[-3:] if len(sorted_hubs) >= 3 else sorted_hubs
        least_accessible.reverse()

        return reachable, unreachable, highly_accessible, least_accessible


