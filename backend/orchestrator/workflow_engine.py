"""Workflow Engine — Main orchestrator executing planning steps and compiling the dashboard state."""

import time
from typing import Dict, Any

from backend.orchestrator.agent_registry import AgentRegistry
from backend.orchestrator.result_aggregator import ResultAggregator
from backend.orchestrator.execution_manager import ExecutionManager
from backend.orchestrator.decision_engine import DecisionEngine
from backend.orchestrator.scheduler import Scheduler

class WorkflowEngine:
    """Enterprise AI Orchestrator running workflow plans and conflict-resolving pipelines."""

    @classmethod
    def get_dashboard_payload(cls) -> Dict[str, Any]:
        """Returns metadata for the AI Orchestrator workspace dashboard."""
        agents = AgentRegistry.get_agents()
        history = Scheduler.get_history()

        # Compute summary metrics
        active_workflows = sum(1 for h in history if h["status"] == "Running")
        avg_decision = int(sum(h["duration_ms"] for h in history) / max(1, len(history)))
        success_rate = round(sum(1 for h in history if h["status"] == "Success") / max(1, len(history)) * 100.0, 1)

        return {
            "agents": agents,
            "history": history,
            "metrics": {
                "active_workflows": active_workflows,
                "avg_decision_time_ms": avg_decision,
                "optimization_success_rate": success_rate,
                "workflow_success_pct": success_rate
            }
        }

    @classmethod
    def run_optimization_workflow(cls, request_params: Dict[str, Any]) -> Dict[str, Any]:
        """Executes multi-agent orchestrator workflows, aggregates data, and resolves conflict recommendations."""
        start_time = time.time()

        # Step 1: Validate request
        if not request_params:
            request_params = {}
        include_reverse = request_params.get("include_reverse", True)

        # Steps 2–7: Execute agents sequentially/asynchronously via ExecutionManager
        steps = ExecutionManager.execute_workflow(request_params)

        # Step 8: Aggregate concrete outputs from services
        aggregated = ResultAggregator.aggregate_data(request_params.get("filters", {}))

        # Step 9-10: Resolve conflicts and generate unified decisions
        decision = DecisionEngine.evaluate(aggregated)

        total_duration = int((time.time() - start_time) * 1000)

        # Record run history
        executed_agent_ids = [s["agent_id"] for s in steps]
        Scheduler.record_run(
            executed_agents=executed_agent_ids,
            duration_ms=total_duration,
            status="Success",
            summary=f"Unified Recommendation: Reroute via {decision['best_route']} (Confidence: {decision['confidence_score']}%)."
        )

        return {
            "workflow_id": f"WF-2026-RUN-{int(time.time()) % 10000}",
            "execution_steps": steps,
            "aggregated_results": aggregated,
            "decision": decision,
            "total_duration_ms": total_duration,
            "status": "Success"
        }
