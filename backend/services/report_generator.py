"""Report Generator — Handles executive templates and historical report downloads."""

import datetime
from typing import Dict, Any, List

from backend.orchestrator.result_aggregator import ResultAggregator
from backend.services.insight_generator import InsightGenerator
from backend.services.executive_summary import ExecutiveSummaryService

REPORT_HISTORY: List[Dict[str, Any]] = [
    {
        "id": "REP-9901",
        "time": "2026-07-18T10:15:30",
        "type": "Weekly Operations Report",
        "generated_by": "System Scheduler",
        "template": "Executive Leadership",
        "downloads": 14,
        "is_favorite": True
    },
    {
        "id": "REP-9902",
        "time": "2026-07-19T16:45:10",
        "type": "Cost Optimization Report",
        "generated_by": "analyst",
        "template": "Regional Manager",
        "downloads": 5,
        "is_favorite": False
    }
]

class ReportGenerator:
    """Aggregates all system metrics, templates, and downloads logs."""

    @classmethod
    def get_history(cls) -> List[Dict[str, Any]]:
        return REPORT_HISTORY

    @classmethod
    def compile_report(cls, report_type: str, template: str, generated_by: str) -> Dict[str, Any]:
        filters = {}
        
        # 1. Aggregate real data
        aggregated = ResultAggregator.aggregate_data(filters)
        
        # 2. Extract explainable insights
        insights = InsightGenerator.generate_insights(filters)

        # 3. Create corporate summary
        summary = ExecutiveSummaryService.get_summary(aggregated)

        # 4. Define template specifics
        focus_areas = {
            "Executive Leadership": ["Financial Impact", "SLA Summary", "Proactive Recommendations"],
            "Operations Manager": ["Congested Hubs", "Transit Delays", "Action Items"],
            "Regional Manager": ["Corridor Performance", "Capacity Limits", "Lanes Detail"],
            "Supply Chain Head": ["Asset Recovery", "Reverse Logistics", "Network Optimization"],
            "Business Analyst": ["Cost Optimization", "Simulation Outputs", "Waterfall Path"]
        }.get(template, ["Overview", "KPIs"])

        # 5. Log in history
        rep_id = f"REP-{datetime.date.today().strftime('%Y-%m%d')}-{len(REPORT_HISTORY)+100}"
        REPORT_HISTORY.insert(0, {
            "id": rep_id,
            "time": datetime.datetime.now().isoformat()[:19],
            "type": report_type,
            "generated_by": generated_by,
            "template": template,
            "downloads": 0,
            "is_favorite": False
        })

        return {
            "report_id": rep_id,
            "generation_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "report_type": report_type,
            "template": template,
            "generated_by": generated_by,
            "summary": summary,
            "insights": insights,
            "focus_areas": focus_areas,
            "aggregated_data": aggregated
        }
