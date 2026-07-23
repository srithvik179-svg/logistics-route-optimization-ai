"""Route Cost & Scoring Engine — Orchestrator with in-memory caching.

Primary entry point for multi-factor route scoring and prioritization. Evaluates cost,
transit times, utilization, partner ratings, and SLA compliance to rank routes.
"""

import json
from typing import Dict, Any, List, Tuple
import numpy as np

from backend.services.repository import repository
from backend.services.graph_engine import GraphEngine
from backend.services.route_score_calculator import RouteScoreCalculator
from backend.models.route_scoring_metrics import (
    RouteScoringPayload,
    RouteScoreResult,
    RouteRankingsSet,
    ComparisonPair,
)
from backend.utils.logger import logger


class RouteScoringEngine:
    """Orchestrates multi-factor route scoring, rankings, and comparison metrics.

    Responsibilities:
        1. Loads graph structures from GraphEngine.
        2. Queries SLA and partner profiles from Repository.
        3. Computes normalized scoring indices.
        4. Compiles rankings and correlations (cheapest vs shortest, fastest vs reliable).
        5. Caches calculated scores.
    """

    _cache: Dict[str, RouteScoringPayload] = {}

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the in-memory cache."""
        cls._cache.clear()
        logger.info("RouteScoringEngine: Cache cleared.")

    @classmethod
    def get_route_scoring_payload(cls, filters: Dict[str, Any]) -> RouteScoringPayload:
        """Main entry point returning a fully computed RouteScoringPayload.

        Args:
            filters: Global filters dictionary.

        Returns:
            RouteScoringPayload payload.
        """
        logger.info(f"RouteScoringEngine: Route Scoring Engine Started. Filters: {filters}")

        # --- Cache Lookup ---
        cache_key = cls._build_cache_key(filters)
        if cache_key in cls._cache:
            logger.info("RouteScoringEngine: Cache HIT — returning cached payload.")
            cached = cls._cache[cache_key]
            cached.cached = True
            return cached

        # --- Load graph payload ---
        graph = GraphEngine.get_graph_payload(filters)
        edges = graph.edges

        if not edges:
            logger.warning("RouteScoringEngine: Empty graph edges registry.")
            empty = cls._empty_payload(filters)
            cls._cache[cache_key] = empty
            return empty

        # Query ratings and compliance statistics
        ratings_map, compliance_map = cls._query_partner_attributes()

        # Build real route-level stats from Logistics_Transactions
        df_tx = repository._processed_sheets.get("Logistics_Transactions")
        route_stats: Dict[str, Dict[str, float]] = {}
        if df_tx is not None and len(df_tx) > 0:
            dest_col = "Destination_Location" if "Destination_Location" in df_tx.columns else ("Destination_Hub" if "Destination_Hub" in df_tx.columns else "Destination_Location")
            if "Origin_Hub" in df_tx.columns and dest_col in df_tx.columns:
                df_tx_work = df_tx.copy()
                df_tx_work["Route_Key"] = df_tx_work["Origin_Hub"].astype(str) + " → " + df_tx_work[dest_col].astype(str)
                cost_col = "Logistics_Cost_Total_USD" if "Logistics_Cost_Total_USD" in df_tx_work.columns else ("Total_Cost_USD" if "Total_Cost_USD" in df_tx_work.columns else "Shipment_Cost")
                
                for r_key, grp in df_tx_work.groupby("Route_Key"):
                    tot = len(grp)
                    met = len(grp[grp["SLA_Breach"].astype(str).str.upper() == "NO"]) if "SLA_Breach" in grp.columns else tot
                    sla_pct = (met / tot * 100.0) if tot > 0 else 95.0
                    avg_c = float(grp[cost_col].mean()) if cost_col in grp.columns else 500.0
                    tot_c = float(grp[cost_col].sum()) if cost_col in grp.columns else avg_c * tot
                    route_stats[r_key] = {
                        "sla_compliance": round(sla_pct, 1),
                        "avg_cost": round(avg_c, 2),
                        "total_cost": round(tot_c, 2)
                    }

        # Compute route scores
        scores: List[RouteScoreResult] = []
        for edge in edges:
            src, dest = edge.source, edge.destination
            partner = edge.logistics_partner
            
            rating = ratings_map.get(partner, 4.0)
            route_key = f"{src} → {dest}"
            r_stat = route_stats.get(route_key, {})
            real_sla = r_stat.get("sla_compliance", compliance_map.get(partner, 95.0))
            real_cost = r_stat.get("avg_cost", edge.cost)
            real_tot_cost = r_stat.get("total_cost", edge.cost * 10.0)

            res = RouteScoreCalculator.calculate_scores(
                src=src,
                dest=dest,
                distance=edge.distance,
                cost=real_cost,
                transit_time=edge.transit_time,
                volume=edge.volume,
                capacity=edge.capacity,
                partner_rating=rating,
                sla_compliance=real_sla,
                total_cost=real_tot_cost
            )
            scores.append(res)

        logger.info("RouteScoringEngine: Route Scores Calculated.")

        # --- Rankings (delegated) ---
        rankings = cls._generate_rankings(scores)
        logger.info("RouteScoringEngine: Business Rankings Generated.")

        # --- Comparison (delegated) ---
        comparisons = cls._perform_comparison(scores)
        logger.info("RouteScoringEngine: Comparison Analysis Completed.")

        # --- Statistics ---
        stats = cls._calculate_statistics(scores)

        # --- Business Insights ---
        insights = cls._generate_business_insights(scores)

        payload = RouteScoringPayload(
            route_scores=scores,
            rankings=rankings,
            comparisons=comparisons,
            statistics=stats,
            business_insights=insights,
            filters_applied=filters,
            cached=False
        )

        # Cache payload
        cls._cache[cache_key] = payload
        logger.info("RouteScoringEngine: Route Score Cache Updated.")
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
    def _query_partner_attributes(cls) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Extracts partner ratings and compliance targets from repository sheets."""
        tpr_sheet_name = "TPR_Master" if repository.sheet_exists("TPR_Master") else "Repair_Center_Master"
        df_tpr = repository._processed_sheets.get(tpr_sheet_name)

        ratings: Dict[str, float] = {}
        compliance: Dict[str, float] = {}

        if df_tpr is not None and len(df_tpr) > 0:
            for _, row in df_tpr.iterrows():
                name = str(row.get("TPR_Name", ""))
                if name:
                    ratings[name] = float(row.get("Rating") or 4.0)
                    compliance[name] = float(row.get("SLA_Compliance_Target") or 95.0)

        return ratings, compliance

    @classmethod
    def _generate_rankings(cls, scores: List[RouteScoreResult]) -> RouteRankingsSet:
        # Sort routes using helper criteria
        best = sorted(scores, key=lambda x: x.overall_route_score, reverse=True)
        cheapest = sorted(scores, key=lambda x: x.cost_score, reverse=True)
        fastest = sorted(scores, key=lambda x: x.transit_time_score, reverse=True)
        reliable = sorted(scores, key=lambda x: x.sla_score, reverse=True)
        capacity = sorted(scores, key=lambda x: x.capacity_score, reverse=True)
        performing = sorted(scores, key=lambda x: x.performance_index, reverse=True)

        return RouteRankingsSet(
            best_routes=[r.route_id for r in best[:10]],
            lowest_cost=[r.route_id for r in cheapest[:10]],
            fastest=[r.route_id for r in fastest[:10]],
            most_reliable=[r.route_id for r in reliable[:10]],
            highest_capacity=[r.route_id for r in capacity[:10]],
            highest_performing=[r.route_id for r in performing[:10]],
            worst_performing=[r.route_id for r in reversed(best[-10:])]
        )

    @classmethod
    def _perform_comparison(cls, scores: List[RouteScoreResult]) -> Dict[str, ComparisonPair]:
        comparisons = {}

        # 1. Distance vs Transit Time
        dists = [r.distance_score for r in scores]
        times = [r.transit_time_score for r in scores]
        corr_dt = cls._correlation(dists, times)
        comparisons["Distance vs Transit Time"] = ComparisonPair(
            metric_a_name="Distance Score",
            metric_b_name="Transit Time Score",
            shared_routes_count=len(scores),
            correlation_coefficient=round(corr_dt, 4),
            differences_summary="Measures routing speed. Positive correlation indicates direct speed alignments."
        )

        # 2. Cost vs Performance
        costs = [r.cost_score for r in scores]
        perfs = [r.performance_index for r in scores]
        corr_cp = cls._correlation(costs, perfs)
        comparisons["Cost vs Performance"] = ComparisonPair(
            metric_a_name="Cost Efficiency Score",
            metric_b_name="Performance Index",
            shared_routes_count=len(scores),
            correlation_coefficient=round(corr_cp, 4),
            differences_summary="Measures value efficiency. High negative correlation flags expensive high-performers."
        )

        # 3. Lowest Cost vs Highest Capacity
        caps = [r.capacity_score for r in scores]
        corr_cc = cls._correlation(costs, caps)
        comparisons["Lowest Cost vs Highest Capacity"] = ComparisonPair(
            metric_a_name="Cost Efficiency Score",
            metric_b_name="Capacity Utilization Score",
            shared_routes_count=len(scores),
            correlation_coefficient=round(corr_cc, 4),
            differences_summary="Measures storage efficiency vs transport expenses."
        )

        # 4. Fastest Route vs Reliable Route
        slas = [r.sla_score for r in scores]
        corr_fr = cls._correlation(times, slas)
        comparisons["Fastest Route vs Reliable Route"] = ComparisonPair(
            metric_a_name="Transit Time Score",
            metric_b_name="SLA Compliance Score",
            shared_routes_count=len(scores),
            correlation_coefficient=round(corr_fr, 4),
            differences_summary="High correlation confirms fast routes remain compliant."
        )

        return comparisons

    @classmethod
    def _correlation(cls, x: List[float], y: List[float]) -> float:
        n = len(x)
        if n < 2:
            return 0.0
        mx, my = sum(x) / n, sum(y) / n
        num = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
        den = (sum((xi - mx)**2 for xi in x) * sum((yi - my)**2 for yi in y))**0.5
        return num / den if den > 0 else 0.0

    @classmethod
    def _calculate_statistics(cls, scores: List[RouteScoreResult]) -> Dict[str, float]:
        overall = [r.overall_route_score for r in scores]
        cost = [r.cost_score for r in scores]
        perf = [r.performance_index for r in scores]

        return {
            "average_route_score": round(sum(overall) / len(overall), 2) if overall else 0.0,
            "max_route_score": max(overall) if overall else 0.0,
            "min_route_score": min(overall) if overall else 0.0,
            "average_operational_cost_score": round(sum(cost) / len(cost), 2) if cost else 0.0,
            "average_route_efficiency_score": round(sum(perf) / len(perf), 2) if perf else 0.0,
            "overall_logistics_performance_score": round(sum(perf) / len(perf), 2) if perf else 0.0
        }

    @classmethod
    def _generate_business_insights(cls, scores: List[RouteScoreResult]) -> Dict[str, List[str]]:
        expensive = []
        low_performing = []
        high_performing = []
        congested = []
        efficient = []
        critical = []

        for r in scores:
            r_id = r.route_id
            if r.cost_score < 40.0:
                expensive.append(r_id)
            if r.overall_route_score < 50.0:
                low_performing.append(r_id)
            if r.overall_route_score > 80.0:
                high_performing.append(r_id)
            if r.capacity_score < 40.0:
                congested.append(r_id)
            if r.cost_score > 80.0:
                efficient.append(r_id)
            if r.operational_risk_score > 70.0:
                critical.append(r_id)

        return {
            "expensive_routes": expensive,
            "low_performing_routes": low_performing,
            "high_performing_routes": high_performing,
            "congested_routes": congested,
            "efficient_routes": efficient,
            "critical_routes": critical
        }

    @classmethod
    def _empty_payload(cls, filters: Dict[str, Any]) -> RouteScoringPayload:
        return RouteScoringPayload(
            route_scores=[],
            rankings=RouteRankingsSet(),
            comparisons={},
            statistics={},
            business_insights={},
            filters_applied=filters,
            cached=False
        )

