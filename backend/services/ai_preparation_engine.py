"""AI Decision Support Preparation Engine — Central orchestrator with in-memory caching.

Prepares logistics decisions by creating standardized decision contexts, normalized
feature vectors, scenario recommendation matrices, and explainability summaries.
"""

import json
import uuid
import time
from typing import Dict, Any, List

from backend.services.graph_engine import GraphEngine
from backend.services.ant_colony_engine import AntColonyEngine
from backend.services.dijkstra_service import DijkstraService
from backend.services.astar_engine import AStarEngine
from backend.services.genetic_algorithm_engine import GeneticAlgorithmEngine
from backend.services.feature_engineering import FeatureEngineeringService
from backend.services.decision_context_builder import DecisionContextBuilder
from backend.services.explainability_service import ExplainabilityService
from backend.models.feature_vector import FeatureVector
from backend.models.recommendation_candidate import RecommendationCandidate
from backend.models.decision_context import AIDecisionSupportPayload
from backend.utils.logger import logger


class AIPreparationEngine:
    """Orchestrates feature extraction, scenario mapping, and explainability compiling."""

    _cache: Dict[str, AIDecisionSupportPayload] = {}

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the in-memory cache."""
        cls._cache.clear()
        logger.info("AI Preparation Cache Updated: cache cleared.")

    @classmethod
    def prepare_decision_support(
        cls,
        source: str,
        destination: str,
        filters: Dict[str, Any]
    ) -> AIDecisionSupportPayload:
        """Compiles decision features matrix, scenario candidates, and explainability data.

        Args:
            source: Starting origin Node ID.
            destination: Destination Node ID target.
            filters: Global filters dictionary.

        Returns:
            AIDecisionSupportPayload: Standardized decision support prepared payload.
        """
        logger.info("AI Preparation Started.")

        # --- Cache Lookup ---
        cache_key = cls._build_cache_key(source, destination, filters)
        if cache_key in cls._cache:
            logger.info("AI Preparation Cache Updated: cache hit returned.")
            cached = cls._cache[cache_key]
            cached.cached = True
            return cached

        # Load Graph layout
        graph = GraphEngine.get_graph_payload(filters)
        nodes = [n.node_id for n in graph.nodes]
        coords = {n.node_id: (n.latitude, n.longitude) for n in graph.nodes}
        neighbor_map = graph.neighbor_mapping

        if source not in neighbor_map or destination not in neighbor_map:
            logger.warning(f"AI Prep warning: Source '{source}' or Destination '{destination}' not in graph. Skipping.")
            empty = cls._empty_payload(source, destination, filters)
            cls._cache[cache_key] = empty
            return empty

        # Run ACO Engine to fetch benchmark solutions comparison list
        aco_payload = AntColonyEngine.optimize_route(source, destination, filters, swarm_size=10, iterations=5)
        benchmarks = aco_payload.benchmarks

        candidates: List[RecommendationCandidate] = []
        feature_matrix: Dict[str, FeatureVector] = {}

        # Mappings of paths for each benchmark algorithm
        for b in benchmarks:
            cand_id = f"cand-{b.algorithm.lower().replace(' ', '-')}-{uuid.uuid4().hex[:6]}"
            
            # Retrieve path node sequence for this benchmark algorithm
            path_seq = [source, destination]
            if b.algorithm == "Dijkstra":
                dist_weight = lambda edge: float(edge.get("distance", 999.0))
                d_res = DijkstraService.find_shortest_path(nodes, neighbor_map, source, destination, dist_weight)
                if d_res and d_res.path_nodes:
                    path_seq = d_res.path_nodes
            elif b.algorithm == "A*":
                a_res = AStarEngine.find_path(nodes, coords, neighbor_map, source, destination, "great-circle")
                if a_res and a_res.path_nodes:
                    path_seq = a_res.path_nodes
            elif b.algorithm == "Genetic Algorithm":
                if aco_payload.optimized_route and b.distance == aco_payload.optimized_route.distance:
                    path_seq = aco_payload.optimized_route.path_nodes
            elif b.algorithm == "Ant Colony Optimization":
                if aco_payload.optimized_route:
                    path_seq = aco_payload.optimized_route.path_nodes

            # Extract features vector
            feat_vec = FeatureEngineeringService.extract_features(
                path_nodes=path_seq,
                distance=b.distance,
                cost=b.cost,
                transit_time=b.transit_time,
                composite_score=b.quality_score
            )

            # Map explainability factor weights
            exp_factors = {
                "transportation_cost_importance": 0.40,
                "transit_time_importance": 0.40,
                "sla_compliance_importance": 0.10
            }

            # Map confidence index
            conf = 0.95 if b.algorithm in ["Dijkstra", "A*"] else 0.88

            candidate = RecommendationCandidate(
                candidate_id=cand_id,
                algorithm=b.algorithm,
                path_nodes=path_seq,
                distance=b.distance,
                cost=b.cost,
                transit_time=b.transit_time,
                is_feasible=b.quality_score > 30.0,
                composite_score=b.quality_score,
                explainability_factors=exp_factors,
                confidence_score=conf
            )

            candidates.append(candidate)
            feature_matrix[cand_id] = feat_vec

        logger.info("Feature Matrix Generated.")

        # Build scenario recommendations options
        scenarios = DecisionContextBuilder.build_scenarios(candidates)
        logger.info("Recommendation Dataset Generated.")

        # Build explainability data
        explainability = ExplainabilityService.generate_explainability_data(candidates)
        logger.info("Explainability Metadata Generated.")

        logger.info("Decision Context Generated.")

        payload = AIDecisionSupportPayload(
            context_id=f"ctx-{source}-to-{destination}",
            source=source,
            destination=destination,
            feature_matrix=feature_matrix,
            scenarios=scenarios,
            explainability=explainability,
            filters_applied=filters,
            cached=False
        )

        cls._cache[cache_key] = payload
        logger.info("AI Preparation Cache Updated: cache updated.")
        return payload

    # ────────────────────────────────────────────
    # Private Helpers
    # ────────────────────────────────────────────

    @classmethod
    def _build_cache_key(cls, source: str, destination: str, filters: Dict[str, Any]) -> str:
        sorted_items = sorted(
            ((k, v) for k, v in filters.items() if v),
            key=lambda x: x[0]
        )
        return json.dumps((source, destination, sorted_items), default=str)

    @classmethod
    def _empty_payload(cls, source: str, destination: str, filters: Dict[str, Any]) -> AIDecisionSupportPayload:
        return AIDecisionSupportPayload(
            context_id=f"ctx-empty-{source}-to-{destination}",
            source=source,
            destination=destination,
            feature_matrix={},
            scenarios={},
            explainability={},
            filters_applied=filters,
            cached=False
        )
