"""Command Center Service — Consolidates and searches across all intelligence workspace nodes."""

import datetime
from typing import Dict, Any, List

from backend.orchestrator.result_aggregator import ResultAggregator

class CommandCenterService:
    """Enterprise Operational intelligence Orchestrator for the Logistics Command Center."""

    @classmethod
    def get_command_center_payload(cls) -> Dict[str, Any]:
        filters = {}
        agg = ResultAggregator.aggregate_data(filters)

        sla_summary = agg["sla_prediction"].get("summary", {})
        sim_summary = agg["simulation"].get("summary", {})
        rev_an      = agg["reverse_logistics"].get("analytics", {})
        corridors   = agg["corridors"].get("corridors", [])

        # Calculate a unified network health score
        sla_comp = sla_summary.get("predicted_sla_compliance", 90.0)
        cost_saving_pct = sim_summary.get("projected_savings_pct", 10.0)
        overall_score = int((sla_comp + (100.0 - cost_saving_pct) + 95.0) / 3)

        # Alerts list with statuses (Unread, Acknowledged, Assigned, Dismissed)
        alerts = [
            {
                "id": "ALT-001",
                "severity": "Critical",
                "color": "#ef4444",
                "type": "Corridor Congestion",
                "message": "Corridor HUB-E → HUB-B delay exceeds 10 hours.",
                "status": "Unread",
                "assigned_to": None
            },
            {
                "id": "ALT-002",
                "severity": "High",
                "color": "#f97316",
                "type": "Shipment SLA Risk",
                "message": "Shipment TXN-1002 has 72.5% SLA breach probability.",
                "status": "Unread",
                "assigned_to": None
            },
            {
                "id": "ALT-003",
                "severity": "Moderate",
                "color": "#f59e0b",
                "type": "Hub Utilization",
                "message": "Hub HUB-D capacity utilization exceeds 60%.",
                "status": "Acknowledged",
                "assigned_to": "Manager-B"
            },
            {
                "id": "ALT-004",
                "severity": "Low",
                "color": "#06b6d4",
                "type": "Reverse Logistics",
                "message": "Texas region recycling volume exceeds weekly target.",
                "status": "Acknowledged",
                "assigned_to": "Analyst-A"
            }
        ]

        # Live Activity feed events
        activity = [
            {"time": "03:45 AM", "event": "SLA Warning issued for shipment TXN-1002", "icon": "fa-hourglass-half", "color": "#ef4444"},
            {"time": "03:30 AM", "event": "Route optimized for lane Austin → Dallas via A* engine", "icon": "fa-compass", "color": "#10b981"},
            {"time": "03:15 AM", "event": "Return initiated for TXN-1008 from Dallas TPR Hub", "icon": "fa-rotate-left", "color": "#06b6d4"},
            {"time": "02:50 AM", "event": "Simulation completed: Driver shifts rescheduled successfully", "icon": "fa-calculator", "color": "#f59e0b"},
            {"time": "02:10 AM", "event": "AI recommendation generated: merge packages on HUB-C → HUB-D", "icon": "fa-brain", "color": "#3b82f6"},
            {"time": "01:30 AM", "event": "Hub Congestion detected at HUB-D (Texas)", "icon": "fa-building", "color": "#f97316"}
        ]

        return {
            "network_health": {
                "overall_score": overall_score,
                "cost_efficiency": int(100 - cost_saving_pct),
                "sla_compliance": int(sla_comp),
                "hub_capacity": 85,
                "route_reliability": 92
            },
            "kpis": {
                "shipments_in_transit": len(agg["sla_prediction"].get("shipments", [])),
                "delayed_shipments": sla_summary.get("high_risk_shipments", 0),
                "critical_alerts": 2,
                "cost_today_usd": round(sum(s.get("shipment_cost", 0) for s in agg["sla_prediction"].get("shipments", [])), 2),
                "avg_sla_percentage": int(sla_comp),
                "hub_utilization_pct": 74.5,
                "vehicle_utilization_pct": 81.2,
                "ai_recommendation_status": "Synchronized"
            },
            "alerts": alerts,
            "activity_feed": activity,
            "aggregated": agg
        }

    @classmethod
    def global_search(cls, query: str) -> List[Dict[str, Any]]:
        """Searches across all shipments, hubs, and corridors based on query string."""
        if not query:
            return []
        q = query.lower()

        filters = {}
        agg = ResultAggregator.aggregate_data(filters)
        shipments = agg["sla_prediction"].get("shipments", [])
        corridors = agg["corridors"].get("corridors", [])
        hubs = agg["sla_prediction"].get("hubs", [])

        results = []

        # Search shipments
        for s in shipments:
            if q in s["transaction_id"].lower() or q in s["origin"].lower() or q in s["destination"].lower():
                results.append({
                    "category": "Shipment",
                    "id": s["transaction_id"],
                    "title": f"Shipment {s['transaction_id']} ({s['origin']} → {s['destination']})",
                    "subtitle": f"Risk Score: {s['risk_score']} | Level: {s['risk_level']}",
                    "target_section": "sla-section"
                })

        # Search hubs
        for h in hubs:
            if q in h["hub"].lower():
                results.append({
                    "category": "Hub",
                    "id": h["hub"],
                    "title": f"Hub {h['hub']} Congestion Matrix",
                    "subtitle": f"Queue Length: {h['queue_length']} | Utilization: {h['capacity_utilization']}%",
                    "target_section": "sla-section"
                })

        # Search corridors
        for c in corridors:
            if q in c["corridor"].lower():
                results.append({
                    "category": "Corridor",
                    "id": c["corridor"],
                    "title": f"Corridor {c['corridor']}",
                    "subtitle": f"SLA Miss Rate: {c['miss_rate']}% | Trend: {c['risk_trend']}",
                    "target_section": "corridor-section"
                })

        return results[:10]  # Cap results at 10 items
