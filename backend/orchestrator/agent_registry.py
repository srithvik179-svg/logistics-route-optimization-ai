"""Agent Registry — Registry of active logistics agents and their current health metrics."""

from typing import Dict, Any, List

# In-memory statistics for demonstration and persistence in running session
AGENT_STATS = {
    "data_ingestion":      {"calls": 42, "errors": 0, "avg_ms": 15},
    "route_analysis":      {"calls": 38, "errors": 0, "avg_ms": 110},
    "corridor_intel":      {"calls": 29, "errors": 0, "avg_ms": 80},
    "cost_optimization":   {"calls": 35, "errors": 0, "avg_ms": 125},
    "sla_prediction":      {"calls": 31, "errors": 0, "avg_ms": 95},
    "reverse_logistics":   {"calls": 18, "errors": 0, "avg_ms": 75},
    "risk_forecasting":    {"calls": 24, "errors": 0, "avg_ms": 90},
    "executive_reporting": {"calls": 50, "errors": 0, "avg_ms": 45}
}

class AgentRegistry:
    """Agent Registry providing static definitions and health of registered agents."""

    @classmethod
    def get_agents(cls) -> List[Dict[str, Any]]:
        return [
            {
                "id": "data_ingestion",
                "name": "Data Ingestion Agent",
                "role": "Loads and validates active spreadsheet/database sources",
                "status": "Healthy",
                "dependency": [],
                "metrics": AGENT_STATS["data_ingestion"]
            },
            {
                "id": "route_analysis",
                "name": "Route Analysis Agent",
                "role": "Analyzes graph connectivity and executes shortest-path pathfinding",
                "status": "Healthy",
                "dependency": ["data_ingestion"],
                "metrics": AGENT_STATS["route_analysis"]
            },
            {
                "id": "corridor_intel",
                "name": "Corridor Intelligence Agent",
                "role": "Evaluates bottleneck transit lanes and lane congestion trends",
                "status": "Healthy",
                "dependency": ["route_analysis"],
                "metrics": AGENT_STATS["corridor_intel"]
            },
            {
                "id": "cost_optimization",
                "name": "Cost Optimization Agent",
                "role": "Optimizes transport cost ratios and runs What-If simulations",
                "status": "Healthy",
                "dependency": ["route_analysis"],
                "metrics": AGENT_STATS["cost_optimization"]
            },
            {
                "id": "sla_prediction",
                "name": "SLA Prediction Agent",
                "role": "Forecasts SLA breach risk levels and delay indicators",
                "status": "Healthy",
                "dependency": ["corridor_intel"],
                "metrics": AGENT_STATS["sla_prediction"]
            },
            {
                "id": "reverse_logistics",
                "name": "Reverse Logistics Agent",
                "role": "Orchestrates returned item streams, refurbishment, and recycling",
                "status": "Healthy",
                "dependency": ["data_ingestion"],
                "metrics": AGENT_STATS["reverse_logistics"]
            },
            {
                "id": "risk_forecasting",
                "name": "Risk Forecasting Agent",
                "role": "Projects rolling 7-day future risk trends across the network",
                "status": "Healthy",
                "dependency": ["sla_prediction"],
                "metrics": AGENT_STATS["risk_forecasting"]
            },
            {
                "id": "executive_reporting",
                "name": "Executive Reporting Agent",
                "role": "Aggregates workspace metrics into compliance and savings charts",
                "status": "Healthy",
                "dependency": ["cost_optimization", "sla_prediction"],
                "metrics": AGENT_STATS["executive_reporting"]
            }
        ]

    @classmethod
    def record_call(cls, agent_id: str, duration_ms: float, success: bool = True):
        if agent_id in AGENT_STATS:
            stats = AGENT_STATS[agent_id]
            stats["calls"] += 1
            if not success:
                stats["errors"] += 1
            # Rolling average
            stats["avg_ms"] = int((stats["avg_ms"] * 9 + duration_ms) / 10)
