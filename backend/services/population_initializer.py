"""Candidate population initializer service for Genetic Algorithm route optimization."""

import random
from typing import List, Dict, Any, Set, Optional
from backend.utils.logger import logger


class PopulationInitializer:
    """Generates the initial set of candidate routes between source and destination.

    Combines high-quality seed paths (A*, Dijkstra) with diverse random walks.
    """

    @classmethod
    def initialize_population(
        cls,
        source: str,
        destination: str,
        population_size: int,
        neighbor_map: Dict[str, List[Dict[str, Any]]],
        astar_path: List[str],
        dijkstra_path: List[str]
    ) -> List[List[str]]:
        """Creates the initial population of route chromosomes.

        Args:
            source: Source Node ID.
            destination: Destination Node ID.
            population_size: Number of chromosomes to generate.
            neighbor_map: Graph adjacency details.
            astar_path: Pre-calculated A* optimal path.
            dijkstra_path: Pre-calculated Dijkstra path.

        Returns:
            List[List[str]]: A list of paths (each path is a list of node IDs).
        """
        logger.info(f"PopulationInitializer: Generating population of size {population_size}.")
        population: List[List[str]] = []

        # 1. Add seeds
        if astar_path:
            population.append(list(astar_path))
        if dijkstra_path and dijkstra_path != astar_path:
            population.append(list(dijkstra_path))

        # 2. Add diverse candidates via random walks
        attempts = 0
        max_attempts = population_size * 10

        while len(population) < population_size and attempts < max_attempts:
            attempts += 1
            path = cls._generate_random_walk(source, destination, neighbor_map)
            if path and path not in population:
                population.append(path)

        # 3. Fallback: if we still need more candidates, clone existing ones
        if not population:
            # Absolute fallback if source and destination are completely isolated
            population.append([source, destination])

        while len(population) < population_size:
            population.append(list(random.choice(population)))

        return population

    @classmethod
    def _generate_random_walk(
        cls,
        source: str,
        destination: str,
        neighbor_map: Dict[str, List[Dict[str, Any]]],
        max_depth: int = 12
    ) -> Optional[List[str]]:
        """Generates a cycle-free random path from source to destination.

        Args:
            source: Source Node ID.
            destination: Destination Node ID.
            neighbor_map: Graph neighbor mapping.
            max_depth: Max depth before backtracking.

        Returns:
            Optional[List[str]]: Path list if found, else None.
        """
        path = [source]
        visited: Set[str] = {source}
        curr = source

        for _ in range(max_depth):
            if curr == destination:
                return path

            neighbors = neighbor_map.get(curr, [])
            unvisited_neighbors = [n["destination"] for n in neighbors if n["destination"] not in visited]

            if not unvisited_neighbors:
                return None  # dead-end

            curr = random.choice(unvisited_neighbors)
            path.append(curr)
            visited.add(curr)

        if path[-1] == destination:
            return path
        return None
