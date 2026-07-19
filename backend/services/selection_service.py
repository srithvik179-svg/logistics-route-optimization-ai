"""Selection service implementing Tournament Selection for Genetic Algorithm parents selection."""

import random
from typing import List
from backend.models.chromosome import Chromosome


class SelectionService:
    """Selects parent chromosomes from the population using tournament selection."""

    @classmethod
    def select_parent(
        cls,
        population: List[Chromosome],
        tournament_size: int = 3
    ) -> Chromosome:
        """Selects a single parent from population using tournament selection.

        Args:
            population: Current list of scored Chromosomes.
            tournament_size: Number of candidates in each tournament.

        Returns:
            Chromosome: Selected parent candidate.
        """
        # Select tournament candidates at random
        candidates = random.sample(population, min(len(population), tournament_size))
        
        # Return candidate with best (highest) fitness
        return max(candidates, key=lambda c: c.fitness)
