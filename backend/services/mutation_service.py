"""Mutation service perturbing paths via randomized walks."""

import random
from typing import List, Dict, Any, Set, Optional


class MutationService:
    """Mutates routes by clearing a sub-path and generating a new random walk."""

    @classmethod
    def mutate(
        cls,
        path: List[str],
        neighbor_map: Dict[str, List[Dict[str, Any]]],
        mutation_rate: float = 0.15
    ) -> List[str]:
        """Mutates a route path sequence if random check passes.

        Args:
            path: Candidate route node ID sequence.
            neighbor_map: Graph neighbor mapping.
            mutation_rate: Mutation probability.

        Returns:
            List[str]: Mutated path (or original path if check fails/fails walk).
        """
        if random.random() > mutation_rate or len(path) < 3:
            return list(path)

        # Pick a random split point (exclude first and last node index)
        split_idx = random.randint(1, len(path) - 2)
        mutated_path = path[:split_idx + 1]
        
        start_node = mutated_path[-1]
        destination = path[-1]
        
        # Walk from split node to destination
        walk = cls._generate_walk_to_dest(
            start_node, destination, neighbor_map, set(mutated_path)
        )

        if walk:
            # Suffix merge
            full_path = mutated_path[:-1] + walk
            # Clean cycle check
            if len(full_path) == len(set(full_path)):
                return full_path

        return list(path)

    @classmethod
    def _generate_walk_to_dest(
        cls,
        start: str,
        dest: str,
        neighbor_map: Dict[str, List[Dict[str, Any]]],
        visited: Set[str],
        max_steps: int = 8
    ) -> Optional[List[str]]:
        """Generates a cycle-free suffix path walk to dest."""
        path = [start]
        curr = start
        local_visited = set(visited)

        for _ in range(max_steps):
            if curr == dest:
                return path

            neighbors = neighbor_map.get(curr, [])
            candidates = [n["destination"] for n in neighbors if n["destination"] not in local_visited]

            if not candidates:
                return None

            curr = random.choice(candidates)
            path.append(curr)
            local_visited.add(curr)

        if path[-1] == dest:
            return path
        return None
