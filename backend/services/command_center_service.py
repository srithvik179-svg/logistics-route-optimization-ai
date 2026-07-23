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
    @classmethod
    def global_search(cls, query: str) -> List[Dict[str, Any]]:
        """Searches across all shipments, hubs, TPRs, parts, corridors, and partners based on query string."""
        if not query or not query.strip():
            return []
        q = query.strip().lower()

        from backend.services.repository import repository
        df_tx = repository._processed_sheets.get("Logistics_Transactions")
        df_hub = repository._processed_sheets.get("Hub_Location_Master")
        tpr_sheet_name = "TPR_Master" if repository.sheet_exists("TPR_Master") else "Repair_Center_Master"
        df_tpr = repository._processed_sheets.get(tpr_sheet_name)
        df_parts = repository._processed_sheets.get("Parts_Master")

        results = []
        seen_ids = set()

        # 1. Search Hubs
        if df_hub is not None and not df_hub.empty:
            for idx, h in df_hub.iterrows():
                hub_id = str(h.get("Hub_ID", ""))
                hub_name = str(h.get("Hub_Name", ""))
                region = str(h.get("Region", ""))
                country = str(h.get("Country", ""))
                if q in hub_id.lower() or q in hub_name.lower() or q in region.lower() or q in country.lower():
                    if hub_id not in seen_ids:
                        seen_ids.add(hub_id)
                        results.append({
                            "category": "Hub",
                            "id": hub_id,
                            "title": f"Hub {hub_id} — {hub_name}",
                            "subtitle": f"Region: {region} | Country: {country}",
                            "target_section": "network-map-section"
                        })

        # 2. Search TPRs / Repair Centers
        if df_tpr is not None and not df_tpr.empty:
            for idx, t in df_tpr.iterrows():
                tpr_id = str(t.get("TPR_ID", ""))
                tpr_name = str(t.get("TPR_Name", ""))
                loc = str(t.get("Location", ""))
                if q in tpr_id.lower() or q in tpr_name.lower() or q in loc.lower():
                    if tpr_id not in seen_ids:
                        seen_ids.add(tpr_id)
                        results.append({
                            "category": "TPR / Repair Center",
                            "id": tpr_id,
                            "title": f"{tpr_id} — {tpr_name}",
                            "subtitle": f"Location: {loc}",
                            "target_section": "corridor-section"
                        })

        # 3. Search Parts
        if df_parts is not None and not df_parts.empty:
            for idx, p in df_parts.iterrows():
                part_no = str(p.get("Part_Number", ""))
                part_name = str(p.get("Part_Name", ""))
                cat = str(p.get("Category", ""))
                if q in part_no.lower() or q in part_name.lower() or q in cat.lower():
                    if part_no not in seen_ids:
                        seen_ids.add(part_no)
                        results.append({
                            "category": "Part Number",
                            "id": part_no,
                            "title": f"Part {part_no} — {part_name}",
                            "subtitle": f"Category: {cat} | Unit Cost: ${p.get('Cost_usd', 0):.2f}",
                            "target_section": "explorer-section"
                        })

        # 4. Search Shipments
        if df_tx is not None and not df_tx.empty:
            for idx, s in df_tx.iterrows():
                txn_id = str(s.get("Transaction_ID", ""))
                orig = str(s.get("Origin_Hub", ""))
                dest = str(s.get("Destination_Hub", ""))
                part_no = str(s.get("Part_Number", ""))
                partner = str(s.get("Logistics_Partner", ""))
                sla = str(s.get("SLA_Breach", "NO"))
                
                if (q in txn_id.lower() or q in orig.lower() or q in dest.lower() or 
                    q in part_no.lower() or q in partner.lower()):
                    if txn_id not in seen_ids:
                        seen_ids.add(txn_id)
                        sla_text = "SLA Breached" if sla.upper() == "YES" else "SLA Compliant"
                        results.append({
                            "category": "Shipment",
                            "id": txn_id,
                            "title": f"Shipment {txn_id} ({orig} → {dest})",
                            "subtitle": f"Part: {part_no} | Partner: {partner} | Status: {sla_text}",
                            "target_section": "sla-section"
                        })

        # 5. Search Corridors
        agg = ResultAggregator.aggregate_data({})
        corridors = agg["corridors"].get("corridors", [])
        for c in corridors:
            orig = c.get("origin", "")
            dest = c.get("destination", "")
            corridor_key = f"{orig} → {dest}"
            if q in orig.lower() or q in dest.lower() or q in corridor_key.lower():
                if corridor_key not in seen_ids:
                    seen_ids.add(corridor_key)
                    results.append({
                        "category": "Corridor",
                        "id": corridor_key,
                        "title": f"Corridor {corridor_key}",
                        "subtitle": f"Shipments: {c.get('shipment_count', 0)} | Delay Rate: {c.get('delay_rate', 0.0)}% | Avg Cost: ${c.get('avg_cost', 0):.2f}",
                        "target_section": "corridor-section"
                    })

        # 6. Search Logistics Partners
        if df_tx is not None and not df_tx.empty and "Logistics_Partner" in df_tx.columns:
            for partner in df_tx["Logistics_Partner"].dropna().unique():
                partner_str = str(partner)
                if q in partner_str.lower():
                    if partner_str not in seen_ids:
                        seen_ids.add(partner_str)
                        results.append({
                            "category": "Logistics Partner",
                            "id": partner_str,
                            "title": f"Partner: {partner_str}",
                            "subtitle": f"Logistics Carrier Partner",
                            "target_section": "performance-section"
                        })

        return results[:12]  # Cap results at top 12 items
