"""Crossover service implementing path-based splicing for route chromosomes."""

import random
from typing import List, Tuple


class CrossoverService:
    """Performs single-point path splicing crossover between two parent routes."""

    @classmethod
    def crossover(
        cls,
        parent_a: List[str],
        parent_b: List[str]
    ) -> Tuple[List[str], List[str]]:
        """Performs crossover by splicing parents at a shared intermediate node.

        Args:
            parent_a: Path node sequence of parent A.
            parent_b: Path node sequence of parent B.

        Returns:
            Tuple[List[str], List[str]]: Two child paths.
        """
        # If paths are too short, no intermediate nodes exist
        if len(parent_a) < 3 or len(parent_b) < 3:
            return list(parent_a), list(parent_b)

        # Find common intermediate nodes (exclude first and last node)
        a_intermediates = set(parent_a[1:-1])
        b_intermediates = set(parent_b[1:-1])
        common = list(a_intermediates.intersection(b_intermediates))

        if not common:
            return list(parent_a), list(parent_b)

        # Splice at a randomly chosen common node
        splice_node = random.choice(common)
        
        idx_a = parent_a.index(splice_node)
        idx_b = parent_b.index(splice_node)

        child_1 = parent_a[:idx_a] + parent_b[idx_b:]
        child_2 = parent_b[:idx_b] + parent_a[idx_a:]

        # Clean cycles (duplicates check)
        if len(child_1) != len(set(child_1)) or len(child_2) != len(set(child_2)):
            return list(parent_a), list(parent_b)

        return child_1, child_2
