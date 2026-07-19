"""Network Optimization Readiness Engine — Orchestrator with in-memory caching.

Primary entry point for preprocessing graph structures for optimization modules.
Maps node indices, normalizes weights, runs consistency checks, and compiles baseline metrics.
"""

import json
from typing import Dict, Any, List
from datetime import datetime

from backend.services.graph_engine import GraphEngine
from backend.services.route_scoring_engine import RouteScoringEngine
from backend.services.graph_preprocessor import GraphPreprocessor
from backend.services.constraint_validator import ConstraintValidator
from backend.services.matrix_generator import MatrixGenerator
from backend.models.optimization_metrics import (
    OptimizationReadinessPayload,
    OptimizationConstraints,
    NetworkBaselines,
    GraphValidationResult,
)
from backend.utils.logger import logger


class OptimizationReadinessEngine:
    """Orchestrates graph preprocessing, dense matrix generations, and integrity validations.

    Responsibilities:
        1. Loads graph representations from GraphEngine.
        2. Retrieves route scoring outputs.
        3. Preprocesses nodes/edges and assigns matrix indices.
        4. Generates dense 2D distance, cost, transit, capacity, and SLA matrices.
        5. Validates network constraints and connectivity.
        6. Caches calculated datasets.
    """

    _cache: Dict[str, OptimizationReadinessPayload] = {}

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the in-memory cache."""
        cls._cache.clear()
        logger.info("OptimizationReadinessEngine: Cache cleared.")

    @classmethod
    def get_readiness_payload(cls, filters: Dict[str, Any]) -> OptimizationReadinessPayload:
        """Main entry point returning a fully preprocessed OptimizationReadinessPayload.

        Args:
            filters: Global filters dictionary.

        Returns:
            OptimizationReadinessPayload payload.
        """
        logger.info(f"OptimizationReadinessEngine: Optimization Readiness Started. Filters: {filters}")

        # --- Cache Lookup ---
        cache_key = cls._build_cache_key(filters)
        if cache_key in cls._cache:
            logger.info("OptimizationReadinessEngine: Cache HIT — returning cached payload.")
            cached = cls._cache[cache_key]
            cached.cached = True
            return cached

        # --- Load graph and scoring payloads ---
        graph = GraphEngine.get_graph_payload(filters)
        scoring = RouteScoringEngine.get_route_scoring_payload(filters)

        if not graph.nodes:
            logger.warning("OptimizationReadinessEngine: Empty graph registry.")
            empty = cls._empty_payload(filters)
            cls._cache[cache_key] = empty
            return empty

        # --- 1. Graph Preprocessing (delegated) ---
        opt_nodes, node_indices = GraphPreprocessor.preprocess_nodes(graph.nodes)
        opt_edges = GraphPreprocessor.preprocess_edges(graph.edges, node_indices)
        logger.info("OptimizationReadinessEngine: Graph Preprocessing Completed.")

        # --- 2. Constraint Validation (delegated) ---
        validation = ConstraintValidator.validate_graph(
            graph.nodes, graph.edges, graph.statistics.connected_components
        )
        logger.info("OptimizationReadinessEngine: Constraint Validation Completed.")

        # --- 3. Dense Matrix Generation (delegated) ---
        d_mat, c_mat, t_mat, cap_mat, sla_mat = MatrixGenerator.generate_matrices(opt_nodes, opt_edges)
        logger.info("OptimizationReadinessEngine: Matrices Generated.")

        # --- 4. Baselines & Constraints ---
        baselines = GraphPreprocessor.calculate_baselines(graph.edges, scoring.route_scores)
        constraints = ConstraintValidator.get_standard_constraints()

        # Metadata dictionary compilation
        metadata = {
            "node_mappings": {n.node_id: n.matrix_index for n in opt_nodes},
            "normalization_reference_distance": 600.0,
            "cost_weight_factor": 0.80,
            "distance_weight_factor": 0.20
        }

        payload = OptimizationReadinessPayload(
            nodes=opt_nodes,
            edges=opt_edges,
            distance_matrix=d_mat,
            cost_matrix=c_mat,
            transit_matrix=t_mat,
            capacity_matrix=cap_mat,
            sla_matrix=sla_mat,
            constraints=constraints,
            baselines=baselines,
            validation=validation,
            metadata=metadata,
            filters_applied=filters,
            cached=False
        )

        # Cache payload
        cls._cache[cache_key] = payload
        logger.info("OptimizationReadinessEngine: Optimization Cache Updated.")
        return payload

    # ────────────────────────────────────────────
    # Private Helpers
    # ────────────────────────────────────────────

    @classmethod
    def _build_cache_key(cls, filters: Dict[str, Any]) -> str:
        sorted_items = sorted(
            ((k, v) for k, v in filters.items() if v),
            key=lambda x: x[0]
        )
        return json.dumps(sorted_items, default=str)

    @classmethod
    def _empty_payload(cls, filters: Dict[str, Any]) -> OptimizationReadinessPayload:
        return OptimizationReadinessPayload(
            nodes=[],
            edges=[],
            distance_matrix=[],
            cost_matrix=[],
            transit_matrix=[],
            capacity_matrix=[],
            sla_matrix=[],
            constraints=OptimizationConstraints(
                max_distance_limit=0.0, max_cost_limit=0.0,
                max_transit_time_limit=0.0, min_sla_target_compliance=0.0
            ),
            baselines=NetworkBaselines(
                baseline_cost=0.0, baseline_transit_time=0.0, baseline_capacity_utilization=0.0,
                baseline_sla_compliance=0.0, baseline_operational_efficiency=0.0,
                baseline_route_performance=0.0
            ),
            validation=GraphValidationResult(
                has_warnings=False, is_valid=False, warnings=[],
                disconnected_components_count=0, has_negative_weights=False,
                has_duplicate_edges=False
            ),
            metadata={},
            filters_applied=filters,
            cached=False
        )
