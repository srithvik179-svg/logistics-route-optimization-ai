"""Report Generator — Handles executive templates and historical report downloads."""

import datetime
from typing import Dict, Any, List

from backend.orchestrator.result_aggregator import ResultAggregator
from backend.services.insight_generator import InsightGenerator
from backend.services.executive_summary import ExecutiveSummaryService

REPORT_HISTORY: List[Dict[str, Any]] = [
    {
        "id": "REP-2026-0723-122",
        "time": "2026-07-23 21:38:11",
        "type": "Executive Summary",
        "generated_by": "analyst",
        "template": "Executive Leadership",
        "downloads": 18,
        "is_favorite": True
    },
    {
        "id": "REP-2026-0723-121",
        "time": "2026-07-23 21:38:06",
        "type": "Network Performance Report",
        "generated_by": "analyst",
        "template": "Regional Manager",
        "downloads": 12,
        "is_favorite": False
    },
    {
        "id": "REP-2026-0723-120",
        "time": "2026-07-23 21:38:03",
        "type": "Network Performance Report",
        "generated_by": "analyst",
        "template": "Regional Manager",
        "downloads": 9,
        "is_favorite": False
    },
    {
        "id": "REP-2026-0723-119",
        "time": "2026-07-23 21:35:55",
        "type": "Network Performance Report",
        "generated_by": "analyst",
        "template": "Regional Manager",
        "downloads": 6,
        "is_favorite": False
    },
    {
        "id": "REP-2026-0723-118",
        "time": "2026-07-23 21:35:54",
        "type": "Network Performance Report",
        "generated_by": "analyst",
        "template": "Regional Manager",
        "downloads": 4,
        "is_favorite": False
    }
]

class ReportGenerator:
    """Aggregates all system metrics, templates, and downloads logs."""

    @classmethod
    def get_history(cls) -> List[Dict[str, Any]]:
        return REPORT_HISTORY

    @classmethod
    def compile_report(cls, report_type: str, template: str, generated_by: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        filters = filters or {}
        
        # 1. Aggregate real data
        aggregated = ResultAggregator.aggregate_data(filters)
        
        # 2. Extract explainable insights
        insights = InsightGenerator.generate_insights(filters)

        # 3. Create corporate summary
        summary = ExecutiveSummaryService.get_summary(aggregated, filters)

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
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": report_type,
            "generated_by": generated_by,
            "template": template,
            "downloads": 1,
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
