"""Scenario Engine — Coordinates comparative outputs and ROI estimates for simulated networks."""

from typing import Dict, Any, List

class ScenarioEngine:
    """Computes comparison variance, annual ROI metrics, and financial waterfall indices."""

    @classmethod
    def compare_scenarios(cls, baseline: Dict[str, Any], simulated: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates difference and cost variance between baseline metrics and simulation values.
        
        Args:
            baseline: Baseline metrics dictionary.
            simulated: Simulated metrics dictionary.
            
        Returns:
            Dict containing comparison results and variance percentages.
        """
        cost_diff = simulated["total_cost"] - baseline["total_cost"]
        cost_change_pct = (cost_diff / baseline["total_cost"]) * 100.0 if baseline["total_cost"] > 0 else 0.0

        transit_diff = simulated["avg_transit_time"] - baseline["avg_transit_time"]
        transit_change_pct = (transit_diff / baseline["avg_transit_time"]) * 100.0 if baseline["avg_transit_time"] > 0 else 0.0

        carbon_diff = simulated["carbon_emissions"] - baseline["carbon_emissions"]
        carbon_change_pct = (carbon_diff / baseline["carbon_emissions"]) * 100.0 if baseline["carbon_emissions"] > 0 else 0.0

        sla_diff = simulated["delivery_success_rate"] - baseline["delivery_success_rate"]

        # Financial Summary ROI Calculations
        # Annual savings: projected savings rescaled from sample volume (assuming sample represents 1 month)
        monthly_savings = max(0.0, -cost_diff)
        annual_savings = monthly_savings * 12.0
        
        # Approximate implementation cost based on scenario complexity
        impl_cost = 25000.0 if cost_diff < 0 else 0.0
        roi_estimate = ((annual_savings - impl_cost) / impl_cost) * 100.0 if impl_cost > 0 else 0.0

        return {
            "cost_diff": round(cost_diff, 2),
            "cost_change_percent": round(cost_change_pct, 1),
            "transit_diff": round(transit_diff, 2),
            "transit_change_percent": round(transit_change_pct, 1),
            "carbon_diff": round(carbon_diff, 1),
            "carbon_change_percent": round(carbon_change_pct, 1),
            "sla_difference": round(sla_diff, 1),
            "projected_monthly_savings": round(monthly_savings, 2),
            "projected_annual_savings": round(annual_savings, 2),
            "roi_percentage": round(max(0.0, roi_estimate), 1),
            "implementation_cost": impl_cost
        }
