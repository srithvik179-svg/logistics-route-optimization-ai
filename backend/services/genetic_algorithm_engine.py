"""Genetic Algorithm Optimization Engine — Orchestrator with in-memory caching.

Evolves route path candidates using tournament selection, single-point splicing,
and random walk mutations to find optimal routing pathways satisfying business constraints.
"""

import json
import time
from typing import Dict, Any, List, Optional

from backend.services.graph_engine import GraphEngine
from backend.services.optimization_readiness_engine import OptimizationReadinessEngine
from backend.services.astar_engine import AStarEngine
from backend.services.dijkstra_service import DijkstraService
from backend.services.population_initializer import PopulationInitializer
from backend.services.fitness_calculator import FitnessCalculator
from backend.services.generation_manager import GenerationManager
from backend.models.chromosome import Chromosome
from backend.models.population import GenerationStats
from backend.models.fitness_result import GeneticOptimizationPayload
from backend.utils.logger import logger


class GeneticAlgorithmEngine:
    """Orchestrates evolutionary logistics path optimization searches.

    Responsibilities:
        1. Loads graph models and constraints datasets.
        2. Queries A* and Dijkstra path seed routes.
        3. Initializes a candidate population.
        4. Evolves candidates over multiple generations checking convergence.
        5. Profiles convergence and population diversity metrics.
        6. Caches results.
    """

    _cache: Dict[str, GeneticOptimizationPayload] = {}

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the in-memory cache."""
        cls._cache.clear()
        logger.info("Genetic Cache Updated: cache cleared.")

    @classmethod
    def optimize_route(
        cls,
        source: str,
        destination: str,
        filters: Dict[str, Any],
        population_size: int = 30,
        generations: int = 20
    ) -> GeneticOptimizationPayload:
        """Runs the evolutionary search to compute the optimal route between nodes.

        Args:
            source: Origin Node ID.
            destination: Destination Node ID.
            filters: Global filters dictionary.
            population_size: Total candidate chromosomes in each generation.
            generations: Maximum generation evolution steps.

        Returns:
            GeneticOptimizationPayload optimization results dataset.
        """
        logger.info("Genetic Algorithm Started.")
        start_time = time.perf_counter()

        # --- Cache Lookup ---
        cache_key = cls._build_cache_key(source, destination, population_size, generations, filters)
        if cache_key in cls._cache:
            logger.info("Genetic Cache Updated: cache hit returned.")
            cached = cls._cache[cache_key]
            cached.cached = True
            return cached

        # --- Load graph and constraints ---
        graph = GraphEngine.get_graph_payload(filters)
        nodes = [n.node_id for n in graph.nodes]
        coords = {n.node_id: (n.latitude, n.longitude) for n in graph.nodes}
        neighbor_map = graph.neighbor_mapping

        # Load constraints
        readiness = OptimizationReadinessEngine.get_readiness_payload(filters)
        constraints = readiness.constraints

        if source not in neighbor_map or destination not in neighbor_map:
            logger.warning(f"Genetic Algorithm warning: Source '{source}' or Destination '{destination}' not in graph.")
            empty = cls._empty_payload(source, destination, filters)
            cls._cache[cache_key] = empty
            return empty

        # Query seeds (A* and Dijkstra)
        astar_res = AStarEngine.find_path(nodes, coords, neighbor_map, source, destination, "great-circle")
        dist_weight = lambda edge: float(edge.get("distance", 999.0))
        dijkstra_res = DijkstraService.find_shortest_path(nodes, neighbor_map, source, destination, dist_weight)

        astar_nodes = astar_res.path_nodes if astar_res else []
        dijkstra_nodes = dijkstra_res.path_nodes if dijkstra_res else []

        # --- 1. Population Initialization ---
        raw_paths = PopulationInitializer.initialize_population(
            source, destination, population_size, neighbor_map, astar_nodes, dijkstra_nodes
        )
        logger.info("Population Generated.")

        # Score initial population
        population: List[Chromosome] = []
        for path in raw_paths:
            scored = FitnessCalculator.calculate_fitness(path, neighbor_map, constraints)
            population.append(scored)
        logger.info("Fitness Calculated.")

        # --- 2. Evolution Loop ---
        fitness_history: List[float] = []
        generation_history: List[GenerationStats] = []
        
        best_overall_chromosome: Optional[Chromosome] = None
        convergence_generation = 0
        best_fitness_value = -1.0

        for gen in range(generations):
            # Compute stats for current generation
            stats = cls._calculate_generation_stats(population, gen)
            generation_history.append(stats)
            
            current_best = max(population, key=lambda c: c.fitness)
            fitness_history.append(current_best.fitness)

            # Keep track of the absolute best chromosome found
            if current_best.fitness > best_fitness_value:
                best_fitness_value = current_best.fitness
                best_overall_chromosome = current_best
                convergence_generation = gen

            # Log generation completion
            logger.info("Generation Completed.")

            # Check convergence (no improvement for 6 generations)
            if gen - convergence_generation >= 6:
                logger.info(f"Genetic Algorithm: Convergence reached at generation {convergence_generation}. Stopping early.")
                break

            # Evolve next generation
            population = GenerationManager.evolve_generation(
                population, neighbor_map, constraints, elitism_count=2
            )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info("Optimization Finished.")

        # Final best candidate selection
        best_sol = best_overall_chromosome
        if best_sol is None:
            # Fallback if population was empty (should not happen)
            best_sol = FitnessCalculator.calculate_fitness([source, destination], neighbor_map, constraints)

        if not best_sol.is_feasible:
            logger.warning("Genetic Algorithm warning: No feasible solution satisfies constraints. Returning best found.")

        # Calculate improvement
        first_best_fit = generation_history[0].best_fitness if generation_history else 1.0
        improvement_pct = ((best_sol.fitness - first_best_fit) / first_best_fit) * 100.0 if first_best_fit > 0 else 0.0

        # Compile execution metadata
        metadata = {
            "execution_time_ms": round(elapsed_ms, 2),
            "convergence_generation": convergence_generation,
            "improvement_percentage": round(improvement_pct, 2),
            "generations_run": len(generation_history),
            "population_size": population_size
        }

        payload = GeneticOptimizationPayload(
            optimized_route=best_sol,
            fitness_history=fitness_history,
            generation_history=generation_history,
            metadata=metadata,
            filters_applied=filters,
            cached=False
        )

        cls._cache[cache_key] = payload
        logger.info("Genetic Cache Updated: cache updated.")
        return payload

    # ────────────────────────────────────────────
    # Private Helpers
    # ────────────────────────────────────────────

    @classmethod
    def _build_cache_key(
        cls,
        source: str,
        destination: str,
        pop_size: int,
        generations: int,
        filters: Dict[str, Any]
    ) -> str:
        sorted_items = sorted(
            ((k, v) for k, v in filters.items() if v),
            key=lambda x: x[0]
        )
        return json.dumps((source, destination, pop_size, generations, sorted_items), default=str)

    @classmethod
    def _calculate_generation_stats(cls, population: List[Chromosome], gen_idx: int) -> GenerationStats:
        fitnesses = [c.fitness for c in population]
        best = max(fitnesses)
        worst = min(fitnesses)
        avg = sum(fitnesses) / len(fitnesses)

        # Diversity: proportion of unique paths
        unique_paths = set(tuple(c.path_nodes) for c in population)
        div = len(unique_paths) / len(population)

        return GenerationStats(
            generation_index=gen_idx,
            best_fitness=round(best, 4),
            average_fitness=round(avg, 4),
            worst_fitness=round(worst, 4),
            diversity=round(div, 4)
        )

    @classmethod
    def _empty_payload(cls, source: str, destination: str, filters: Dict[str, Any]) -> GeneticOptimizationPayload:
        penalized_route = Chromosome(
            path_nodes=[source, destination],
            fitness=0.0001,
            is_feasible=False,
            distance=999999.0,
            cost=999999.0,
            transit_time=999999.0,
            capacity_utilization=0.0,
            sla_compliance=0.0,
            reliability_score=0.0,
            operational_efficiency=0.0
        )
        return GeneticOptimizationPayload(
            optimized_route=penalized_route,
            fitness_history=[0.0001],
            generation_history=[],
            metadata={},
            filters_applied=filters,
            cached=False
        )
