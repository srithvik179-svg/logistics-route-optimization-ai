"""Corridor Service — Coordinates corridor health checks, bottleneck audits, and AI improvement suggestions."""

from typing import Dict, Any, List
import pandas as pd

from backend.services.route_analysis_service import RouteAnalysisService
from backend.analytics.corridor_metrics import CorridorMetrics
from backend.utils.logger import logger

class CorridorService:
    """Service providing corridor analysis payloads and strategic recommendations."""

    @classmethod
    def get_corridor_intelligence(cls, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Compiles scoring data, highlights bottlenecks, and drafts optimization suggestions.
        
        Args:
            filters: Global filters dictionary.
            
        Returns:
            Dict containing detailed corridor analytics.
        """
        logger.info("CorridorService: Fetching corridor intelligence payload.")

        # 1. Fetch routes from active network
        analysis = RouteAnalysisService.get_route_analysis_payload(filters)
        raw_routes = analysis.get("routes", [])

        # 2. Enrich routes with normalized metrics
        enriched_routes = CorridorMetrics.calculate_corridor_scores(raw_routes)

        if not enriched_routes:
            return {
                "corridors": [],
                "network_health_score": 100.0,
                "top_efficient": [],
                "top_inefficient": [],
                "most_delayed": [],
                "highest_cost": [],
                "recommendations": [],
                "bottlenecks": []
            }

        # Sort variants for executive widgets
        sorted_by_eff = sorted(enriched_routes, key=lambda x: x["efficiency_score"], reverse=True)
        top_efficient = sorted_by_eff[:10]
        top_inefficient = sorted_by_eff[-10:][::-1]

        most_delayed = sorted(enriched_routes, key=lambda x: x["delay_frequency"], reverse=True)[:10]
        highest_cost = sorted(enriched_routes, key=lambda x: x["avg_cost"], reverse=True)[:10]

        # Calculate Overall Network Health Index (average efficiency score)
        health_score = round(sum([r["efficiency_score"] for r in enriched_routes]) / len(enriched_routes), 1)

        # 3. Generate Actionable AI Recommendations (data-driven)
        recommendations = []
        bottlenecks = []

        for r in enriched_routes:
            orig = r["origin"]
            dest = r["destination"]
            eff = r["efficiency_score"]
            delay = r["delay_frequency"]
            cost = r["avg_cost"]
            util = r["capacity_utilization"]

            # Bottleneck detection triggers
            if eff < 50.0:
                bottlenecks.append({
                    "corridor": f"{orig} → {dest}",
                    "type": "Low Efficiency Corridor",
                    "details": f"Overall efficiency score of {eff}/100. Average delay: {delay}%.",
                    "severity": "High"
                })
                
                # Recommendation
                recommendations.append({
                    "corridor": f"{orig} → {dest}",
                    "suggestion": f"Shift high-priority shipments from {orig} to alternative transit hubs to bypass {dest}.",
                    "impact": "Improves delivery SLA compliance by avoiding high-congestion segments.",
                    "priority": "High"
                })

            if delay > 30.0:
                bottlenecks.append({
                    "corridor": f"{orig} → {dest}",
                    "type": "Frequent SLA Breaches",
                    "details": f"Corridor has an active delay rate of {delay}%.",
                    "severity": "Critical"
                })
                
                partners = ", ".join(r.get("partners", ["partner"]))
                recommendations.append({
                    "corridor": f"{orig} → {dest}",
                    "suggestion": f"Audit logistics service provider ({partners}) performance SLA metrics on this corridor.",
                    "impact": "Reduces transit delay ratios by enforcing partner service thresholds.",
                    "priority": "Critical"
                })

            if cost > 250.0:
                bottlenecks.append({
                    "corridor": f"{orig} → {dest}",
                    "type": "High Cost Corridor",
                    "details": f"Average transportation fee stands at ${cost:.2f}.",
                    "severity": "Medium"
                })
                
                recommendations.append({
                    "corridor": f"{orig} → {dest}",
                    "suggestion": "Consolidate low-priority parts shipments into larger freight batches or use Ground transport.",
                    "impact": "Lowers carbon emissions and transportation costs by optimizing container load volume.",
                    "priority": "Medium"
                })

            if util < 25.0:
                bottlenecks.append({
                    "corridor": f"{orig} → {dest}",
                    "type": "Underutilized Corridor",
                    "details": f"Capacity utilization is critically low at {util}%.",
                    "severity": "Low"
                })
                
                recommendations.append({
                    "corridor": f"{orig} → {dest}",
                    "suggestion": f"Reallocate standby carrier capacities from the {orig} corridor to higher-demand networks.",
                    "impact": "Maximizes asset efficiency and balances network-wide capacity.",
                    "priority": "Low"
                })

        # Provide a default recommendation if none triggered
        if not recommendations:
            recommendations.append({
                "corridor": "All Corridors",
                "suggestion": "Logistics corridors are operating within optimal bounds. Maintain current asset distributions.",
                "impact": "Preserves stable operations and steady cost structures.",
                "priority": "Low"
            })

        return {
            "corridors": enriched_routes,
            "network_health_score": health_score,
            "top_efficient": top_efficient,
            "top_inefficient": top_inefficient,
            "most_delayed": most_delayed,
            "highest_cost": highest_cost,
            "recommendations": recommendations,
            "bottlenecks": bottlenecks
        }
