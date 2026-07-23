"""Simulation Service — Orchestrates baseline loading, parameter mapping, and suggestions compiler."""

from typing import Dict, Any, List
import pandas as pd

from backend.services.repository import repository
from backend.analytics.cost_simulation import CostSimulation
from backend.services.scenario_engine import ScenarioEngine
from backend.utils.logger import logger

class SimulationService:
    """Orchestrates What-If Simulations, charts datasets, and generates AI tips."""

    @classmethod
    def get_simulation_payload(cls, filters: Dict[str, Any], scenarios: Dict[str, Any]) -> Dict[str, Any]:
        """Loads baseline transactions, applies what-if overrides, and returns comparison report.
        
        Args:
            filters: Global filters dict.
            scenarios: What-If override parameters.
            
        Returns:
            Dict containing comparison overview, charts, and recommendations.
        """
        logger.info("SimulationService: Preparing What-If Simulation payload.")

        # 1. Fetch raw transaction data
        df_tx = repository._processed_sheets.get("Logistics_Transactions")
        if df_tx is None or df_tx.empty:
            df_tx = pd.DataFrame()

        # Apply filters to baseline
        from backend.services.bi_service import BIService
        df_baseline = BIService.apply_filters(df_tx, filters)

        # 2. Run Baseline metrics calculation
        baseline_metrics = CostSimulation.run_simulation(df_baseline, {})

        # 3. Run Simulated metrics calculation
        simulated_metrics = CostSimulation.run_simulation(df_baseline, scenarios)

        # 4. Generate comparison metrics
        comparison = ScenarioEngine.compare_scenarios(baseline_metrics, simulated_metrics)

        # 5. Generate AI suggestions (data-driven)
        recommendations = []
        cost_diff = comparison["cost_diff"]
        sla_diff = comparison["sla_difference"]
        carbon_diff = comparison["carbon_diff"]

        if cost_diff > 0:
            recommendations.append({
                "title": "Cost Overrun Alert",
                "recommendation": "This scenario increases overall logistics expenses. Consider consolidating shipment schedules or swapping premium air corridors with ground lanes.",
                "benefit": "Limits operational budget drain and balances container capacity."
            })
        elif cost_diff < 0:
            recommendations.append({
                "title": "Cost Saving Opportunity",
                "recommendation": "Implement this optimized layout to save significant overhead. Merge smaller shipments on low-frequency lanes.",
                "benefit": f"Reduces transportation costs by {abs(comparison['cost_change_percent'])}%."
            })

        if sla_diff < 0:
            recommendations.append({
                "title": "SLA Compliance Warning",
                "recommendation": "Proposed adjustments trigger delivery delays. Allocate buffer capacities at regional hubs.",
                "benefit": "Protects vendor credibility scores and keeps delivery failure rate low."
            })

        if carbon_diff > 0:
            recommendations.append({
                "title": "Carbon Footprint Alert",
                "recommendation": "Increased fuel consumption detected. Reallocate shipments to low-emission logistics partners.",
                "benefit": "Maintains corporate sustainability values and lowers fuel taxes."
            })

        # Default recommendations if none triggered
        if not recommendations:
            recommendations.append({
                "title": "Corridor Optimization Tip",
                "recommendation": "Maintain baseline operations. Current shipment distributions are cost-efficient and meet SLA targets.",
                "benefit": "Preserves stable margins and service level metrics."
            })

        # 6. Build Chart datasets for visualization
        # Cost Breakdown (current vs simulated)
        cost_breakdown = {
            "categories": ["Transportation", "Fuel Cost", "Base overhead"],
            "baseline": [
                baseline_metrics["transportation_cost"],
                baseline_metrics["fuel_cost"],
                baseline_metrics["total_cost"] * 0.10
            ],
            "simulated": [
                simulated_metrics["transportation_cost"],
                simulated_metrics["fuel_cost"],
                simulated_metrics["total_cost"] * 0.10
            ]
        }

        # Waterfall chart data: Baseline -> Fuel -> Driver -> Maintenance -> Simulated
        waterfall_data = {
            "labels": ["Baseline", "Fuel Delta", "Driver Delta", "Maint Delta", "Simulated"],
            "values": [
                baseline_metrics["total_cost"],
                (simulated_metrics["total_cost"] - baseline_metrics["total_cost"]) * 0.35,
                (simulated_metrics["total_cost"] - baseline_metrics["total_cost"]) * 0.45,
                (simulated_metrics["total_cost"] - baseline_metrics["total_cost"]) * 0.20,
                simulated_metrics["total_cost"]
            ]
        }

        return {
            "baseline": baseline_metrics,
            "simulated": simulated_metrics,
            "comparison": comparison,
            "recommendations": recommendations,
            "charts": {
                "cost_breakdown": cost_breakdown,
                "waterfall": waterfall_data
            }
        }
