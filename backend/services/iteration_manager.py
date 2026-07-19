"""Iteration manager service coordinating ant paths construction and iteration stats compiling."""

from typing import List, Dict, Any, Tuple
from backend.models.ant import Ant
from backend.models.aco_result import ACOIterationStats
from backend.models.optimization_metrics import OptimizationConstraints
from backend.services.transition_probability import TransitionProbabilityService
from backend.services.fitness_calculator import FitnessCalculator
from backend.utils.logger import logger


class IterationManager:
    """Manages ant path constructions and compiles stats for each iteration cycle."""

    @classmethod
    def run_iteration(
        cls,
        iteration_idx: int,
        swarm_size: int,
        source: str,
        destination: str,
        neighbor_map: Dict[str, List[Dict[str, Any]]],
        pheromone_matrix: Dict[str, Dict[str, float]],
        constraints: OptimizationConstraints,
        alpha: float = 1.0,
        beta: float = 2.0,
        max_steps: int = 15
    ) -> Tuple[List[Ant], ACOIterationStats]:
        """Runs route search constructions for the swarm and updates stats.

        Args:
            iteration_idx: Current iteration counter.
            swarm_size: Swarm size count.
            source: Origin Node ID.
            destination: Destination Node ID.
            neighbor_map: Adjacency details.
            pheromone_matrix: Pheromone matrix levels.
            constraints: Optimization constraints thresholds.
            alpha: Pheromone weight.
            beta: Heuristic visibility weight.
            max_steps: Maximum hops limit before backtracking search stops.

        Returns:
            Tuple[List[Ant], ACOIterationStats]: Evaluated ants and statistics.
        """
        ants: List[Ant] = []

        for _ in range(swarm_size):
            path_nodes = [source]
            visited = {source}
            curr = source

            # Construct path hop by hop
            for _ in range(max_steps):
                if curr == destination:
                    break

                next_node = TransitionProbabilityService.select_next_node(
                    curr, visited, neighbor_map, pheromone_matrix, alpha, beta
                )

                if next_node is None:
                    break  # stuck

                path_nodes.append(next_node)
                visited.add(next_node)
                curr = next_node

            # Evaluate path stats using FitnessCalculator
            scored = FitnessCalculator.calculate_fitness(path_nodes, neighbor_map, constraints)
            
            # If the ant did not reach the destination, penalize fitness heavily
            fitness_val = scored.fitness
            if path_nodes[-1] != destination:
                fitness_val = 0.0001

            ants.append(Ant(
                path_nodes=path_nodes,
                distance=scored.distance,
                cost=scored.cost,
                transit_time=scored.transit_time,
                is_feasible=scored.is_feasible and path_nodes[-1] == destination,
                fitness=round(fitness_val, 4)
            ))

        # Compile iteration statistics
        stats = cls._compile_stats(ants, iteration_idx, destination)
        logger.info("Iteration Completed.")
        return ants, stats

    @classmethod
    def _compile_stats(cls, ants: List[Ant], gen_idx: int, destination: str) -> ACOIterationStats:
        fitnesses = [a.fitness for a in ants]
        best = max(fitnesses) if fitnesses else 0.0
        worst = min(fitnesses) if fitnesses else 0.0
        avg = sum(fitnesses) / len(fitnesses) if fitnesses else 0.0

        paths_found = sum(1 for a in ants if a.path_nodes[-1] == destination)

        return ACOIterationStats(
            iteration_index=gen_idx,
            best_fitness=round(best, 4),
            average_fitness=round(avg, 4),
            worst_fitness=round(worst, 4),
            paths_found_count=paths_found
        )
