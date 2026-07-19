"""Generation manager service coordinating evolutionary selection, crossover, and mutation."""

from typing import List, Dict, Any
from backend.models.chromosome import Chromosome
from backend.models.optimization_metrics import OptimizationConstraints
from backend.services.selection_service import SelectionService
from backend.services.crossover_service import CrossoverService
from backend.services.mutation_service import MutationService
from backend.services.fitness_calculator import FitnessCalculator


class GenerationManager:
    """Manages generational transitions by applying selection, elitism, crossover, and mutation."""

    @classmethod
    def evolve_generation(
        cls,
        parent_population: List[Chromosome],
        neighbor_map: Dict[str, List[Dict[str, Any]]],
        constraints: OptimizationConstraints,
        crossover_rate: float = 0.80,
        mutation_rate: float = 0.15,
        elitism_count: int = 2
    ) -> List[Chromosome]:
        """Evolves the current population list to the next generation.

        Args:
            parent_population: List of Chromosomes in the current generation.
            neighbor_map: Graph adjacency details.
            constraints: Network-wide constraints thresholds.
            crossover_rate: Crossover probability.
            mutation_rate: Mutation probability.
            elitism_count: Number of top chromosomes preserved directly.

        Returns:
            List[Chromosome]: Scored chromosomes for the next generation.
        """
        population_size = len(parent_population)
        
        # Sort by fitness descending
        sorted_parents = sorted(parent_population, key=lambda c: c.fitness, reverse=True)

        # 1. Elitism: preserve top best chromosomes
        new_generation_paths: List[List[str]] = [
            list(c.path_nodes) for c in sorted_parents[:elitism_count]
        ]

        # 2. Reproduction loop
        while len(new_generation_paths) < population_size:
            # Selection
            parent_a = SelectionService.select_parent(sorted_parents)
            parent_b = SelectionService.select_parent(sorted_parents)

            # Crossover
            child_a, child_b = CrossoverService.crossover(parent_a.path_nodes, parent_b.path_nodes)

            # Mutation
            child_a = MutationService.mutate(child_a, neighbor_map, mutation_rate)
            child_b = MutationService.mutate(child_b, neighbor_map, mutation_rate)

            new_generation_paths.append(child_a)
            # Ensure we don't exceed population size when adding child_b
            if len(new_generation_paths) < population_size:
                new_generation_paths.append(child_b)

        # 3. Evaluate fitness of the new generation
        next_population = []
        for path in new_generation_paths:
            scored = FitnessCalculator.calculate_fitness(path, neighbor_map, constraints)
            next_population.append(scored)

        return next_population
