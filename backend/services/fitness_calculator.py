"""Fitness calculation service evaluating route candidates and checking constraints."""

from typing import List, Dict, Any, Tuple
from backend.models.chromosome import Chromosome
from backend.models.optimization_metrics import OptimizationConstraints


class FitnessCalculator:
    """Evaluates logistics candidate paths for distance, cost, time, and constraint compliance."""

    @classmethod
    def calculate_fitness(
        cls,
        path_nodes: List[str],
        neighbor_map: Dict[str, List[Dict[str, Any]]],
        constraints: OptimizationConstraints
    ) -> Chromosome:
        """Evaluates path chromosome, returning its fitness and metrics.

        Args:
            path_nodes: Candidate route node ID sequence.
            neighbor_map: Graph adjacency attributes mapping.
            constraints: Optimization constraints thresholds.

        Returns:
            Chromosome model with computed scores.
        """
        if len(path_nodes) < 2:
            return cls._penalized_chromosome(path_nodes, "Invalid path length")

        tot_dist = 0.0
        tot_cost = 0.0
        tot_time = 0.0
        
        utilizations = []
        sla_compliances = []
        reliability_scores = []

        is_valid_topology = True
        capacity_violated = False

        for i in range(len(path_nodes) - 1):
            u, v = path_nodes[i], path_nodes[i+1]
            
            # Find edge in neighbor map
            edge = None
            for e in neighbor_map.get(u, []):
                if e["destination"] == v:
                    edge = e
                    break

            if edge is None:
                is_valid_topology = False
                break

            tot_dist += edge.get("distance", 0.0)
            tot_cost += edge.get("cost", 0.0)
            tot_time += edge.get("transit_time", 0.0)

            # Capacity utilization
            vol = edge.get("volume", 0.0)
            cap = edge.get("capacity", 1.0)
            if cap <= 0:
                cap = 1.0
            util = vol / cap
            utilizations.append(util)

            if vol > cap:
                capacity_violated = True

            # Nominals
            sla_compliances.append(95.0)  # default nominal
            reliability_scores.append(90.0)  # default nominal

        if not is_valid_topology:
            return cls._penalized_chromosome(path_nodes, "Graph connection violation")

        # Constraints validation
        is_feasible = True
        if tot_dist > constraints.max_distance_limit:
            is_feasible = False
        if tot_cost > constraints.max_cost_limit:
            is_feasible = False
        if tot_time > constraints.max_transit_time_limit:
            is_feasible = False
        if capacity_violated:
            is_feasible = False

        avg_util = sum(utilizations) / len(utilizations) if utilizations else 0.0
        avg_sla = sum(sla_compliances) / len(sla_compliances) if sla_compliances else 95.0
        avg_rel = sum(reliability_scores) / len(reliability_scores) if reliability_scores else 90.0

        # Composite fitness score: maximize SLA, minimize cost/time
        # fitness = 1000 / (Cost + 15 * Time + 0.1 * Distance + 1)
        denom = tot_cost * 0.40 + tot_time * 20.0 + tot_dist * 0.05 + 1.0
        fitness = 1000.0 / denom

        # Apply penalty for infeasible chromosomes
        if not is_feasible:
            fitness *= 0.10

        # Calculate operational efficiency scorecard
        oper_eff = max(0.0, min(100.0, avg_sla * 0.50 + avg_rel * 0.30 + (1.0 - avg_util) * 20.0))

        return Chromosome(
            path_nodes=path_nodes,
            fitness=round(fitness, 4),
            is_feasible=is_feasible,
            distance=round(tot_dist, 2),
            cost=round(tot_cost, 2),
            transit_time=round(tot_time, 2),
            capacity_utilization=round(avg_util, 4),
            sla_compliance=round(avg_sla, 2),
            reliability_score=round(avg_rel, 2),
            operational_efficiency=round(oper_eff, 2)
        )

    @classmethod
    def _penalized_chromosome(cls, path_nodes: List[str], reason: str) -> Chromosome:
        """Helper to build highly penalized Chromosome."""
        return Chromosome(
            path_nodes=path_nodes,
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
