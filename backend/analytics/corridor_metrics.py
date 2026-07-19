"""Corridor Metrics Engine — Computes normalized performance scores for transport lanes."""

from typing import Dict, Any, List

class CorridorMetrics:
    """Calculates efficiency, reliability, congestion, cost efficiency, and risk scores."""

    @classmethod
    def calculate_corridor_scores(cls, routes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Processes each route, calculates scoring attributes, and normalizes them to 0-100.
        
        Args:
            routes: Raw list of route dictionaries from RouteAnalysisService.
            
        Returns:
            List of routes enriched with efficiency metrics.
        """
        if not routes:
            return []

        # Find max metrics for normalization
        max_volume = max([r["shipment_count"] for r in routes]) if routes else 1
        max_cost_per_mile = max([r["avg_cost"] / max(1.0, r["distance"]) for r in routes]) if routes else 1.0

        enriched_routes = []
        for r in routes:
            dist = r["distance"]
            vol = r["shipment_count"]
            avg_cost = r["avg_cost"]
            delay_rate = r["delay_rate"]

            # 1. Throughput Score (0-100)
            throughput = min(100.0, round((vol / max_volume) * 100.0, 1))

            # 2. Delay Frequency (0-100)
            delay_freq = min(100.0, round(delay_rate, 1))

            # 3. Reliability Score (0-100)
            reliability = round(100.0 - delay_freq, 1)

            # 4. Cost Efficiency (0-100)
            cost_per_mile = avg_cost / max(1.0, dist)
            # Inverse score: lower cost per mile -> higher efficiency
            cost_eff = round(max(0.0, 100.0 - (cost_per_mile / max_cost_per_mile) * 80.0), 1)

            # 5. Congestion Score (0-100)
            # Combines volume weight and delay frequency
            congestion = min(100.0, round((throughput * 0.6) + (delay_freq * 0.4), 1))

            # 6. Capacity Utilization (0-100)
            # Approximated: 80% is optimal load, higher is overloaded, lower is underutilized
            cap_util = min(100.0, round((vol / max(1.0, max_volume * 0.8)) * 100.0, 1))

            # 7. Risk Score (0-100)
            # Delay frequency + distance complexity + congestion load
            dist_factor = 25.0 if dist > 500.0 else (10.0 if dist > 200.0 else 5.0)
            risk = min(100.0, round((delay_freq * 0.5) + (congestion * 0.3) + dist_factor, 1))

            # 8. Carbon Estimate (kg CO2)
            # 0.15 gallons per mile * 10.15 kg CO2 per gallon * distance (in km, converted from miles weight)
            carbon = round(dist * 0.15 * 10.15, 1)

            # 9. Overall Efficiency Score (0-100)
            # Weighted average: 40% Reliability, 40% Cost Efficiency, 20% optimal load (100 - Congestion)
            efficiency = min(100.0, max(0.0, round(
                (reliability * 0.4) + (cost_eff * 0.4) + ((100.0 - congestion) * 0.2), 1
            )))

            # Bottleneck detection flags
            is_slow = avg_cost > 150.0 and delay_rate > 35.0
            is_overloaded = vol >= max_volume * 0.75
            is_underutilized = cap_util < 25.0

            enriched_routes.append({
                **r,
                "efficiency_score": efficiency,
                "congestion_score": congestion,
                "reliability_score": reliability,
                "cost_efficiency": cost_eff,
                "risk_score": risk,
                "capacity_utilization": cap_util,
                "delay_frequency": delay_freq,
                "shipment_throughput": throughput,
                "carbon_estimate": carbon,
                "is_slow": is_slow,
                "is_overloaded": is_overloaded,
                "is_underutilized": is_underutilized
            })

        return enriched_routes
