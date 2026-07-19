"""Scheduler — Mock workflow job task scheduling and queues."""

from typing import Dict, Any, List
import datetime

# Mock workflow history to keep logs in memory during server lifetime
WORKFLOW_HISTORY: List[Dict[str, Any]] = [
    {
        "id": "WF-2026-0718",
        "time": "2026-07-18T14:22:15",
        "agents": ["data_ingestion", "route_analysis", "sla_prediction", "executive_reporting"],
        "duration_ms": 320,
        "status": "Success",
        "summary": "Verified standard operational SLAs; no critical bottlenecks detected."
    },
    {
        "id": "WF-2026-0719",
        "time": "2026-07-19T09:05:44",
        "agents": ["data_ingestion", "route_analysis", "cost_optimization", "sla_prediction", "corridor_intel", "executive_reporting"],
        "duration_ms": 415,
        "status": "Success",
        "summary": "Resolved cost-saving conflict in Houston lanes; SLA targets maintained."
    }
]

class Scheduler:
    """Manages active job timelines and logs execution history."""

    @classmethod
    def get_history(cls) -> List[Dict[str, Any]]:
        return WORKFLOW_HISTORY

    @classmethod
    def record_run(cls, executed_agents: List[str], duration_ms: int, status: str, summary: str) -> str:
        wf_id = f"WF-{datetime.date.today().strftime('%Y-%m%d')}-{len(WORKFLOW_HISTORY)+100}"
        run_log = {
            "id": wf_id,
            "time": datetime.datetime.now().isoformat()[:19],
            "agents": executed_agents,
            "duration_ms": duration_ms,
            "status": status,
            "summary": summary
        }
        WORKFLOW_HISTORY.insert(0, run_log)
        return wf_id
