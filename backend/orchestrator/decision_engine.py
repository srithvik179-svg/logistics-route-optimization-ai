"""Decision Engine — Resolves conflicts between agent recommendations and derives unified logistics decisions."""

from typing import Dict, Any, List

class DecisionEngine:
    """Combines metrics from multiple services to produce a unified recommendation."""

    @classmethod
    def evaluate(cls, aggregated: Dict[str, Any]) -> Dict[str, Any]:
        sla_summary = aggregated["sla_prediction"].get("summary", {})
        sim_summary = aggregated["simulation"].get("summary", {})
        corridors   = aggregated["corridors"].get("corridors", [])
        reverse_an  = aggregated["reverse_logistics"].get("analytics", {})

        from backend.services.repository import repository
        df_hub = repository._processed_sheets.get("Hub_Location_Master")
        tpr_sheet_name = "TPR_Master" if repository.sheet_exists("TPR_Master") else "Repair_Center_Master"
        df_tpr = repository._processed_sheets.get(tpr_sheet_name)
        
        hubs_list = list(df_hub["Hub_ID"].unique()) if df_hub is not None and len(df_hub) > 0 and "Hub_ID" in df_hub.columns else []
        tpr_list = list(df_tpr["TPR_Name"].unique()) if df_tpr is not None and len(df_tpr) > 0 and "TPR_Name" in df_tpr.columns else ["Refurbishment Center"]
        
        hub1 = hubs_list[0] if len(hubs_list) > 0 else "Origin Hub"
        hub2 = hubs_list[1] if len(hubs_list) > 1 else ("Destination Hub" if len(hubs_list) > 0 else "Destination")
        tpr1 = tpr_list[0] if len(tpr_list) > 0 else "Refurbishment Center"

        # Find best routing corridor (lowest cost, highest SLA compliance)
        best_route = f"{hub1} → {hub2}"
        lowest_cost_route = f"{hub2} → {hub1}"
        lowest_cost_val = float('inf')
        highest_sla_val = 0.0

        for c in corridors:
            cost = c.get("avg_cost", 9999.0)
            sla_compliance = 100.0 - c.get("miss_rate", 0.0)
            if cost < lowest_cost_val:
                lowest_cost_val = cost
                lowest_cost_route = c.get("corridor", lowest_cost_route)
            if sla_compliance > highest_sla_val:
                highest_sla_val = sla_compliance
                best_route = c.get("corridor", best_route)

        # Confidence Score calculation
        base_confidence = 90.0
        # Congestion/SLA penalties
        sla_miss_penalty = (100.0 - sla_summary.get("predicted_sla_compliance", 100.0)) * 0.4
        confidence = round(base_confidence - sla_miss_penalty, 1)
        confidence = max(50.0, min(99.0, confidence))

        # Conflict resolution logic:
        # Conflict: Cost optimization suggests reducing lanes (to save cost),
        # but SLA prediction flags those lanes as high-risk/congested (requiring more capacity).
        conflicts = []
        if sim_summary.get("projected_annual_savings", 0) > 0 and sla_summary.get("high_risk_shipments", 0) > 2:
            conflicts.append({
                "type": "Cost vs. SLA Congestion",
                "description": "Cost optimization recommends lane consolidations, but SLA Prediction warns of high-risk cargo backlog at destination hubs.",
                "resolution": f"Override cost reduction: Prioritize capacity on {best_route} to maintain SLA compliance, but apply mode shift optimizations elsewhere."
            })

        # Compile business and network impacts
        biz_impact = f"Mitigates up to ${sla_summary.get('high_risk_shipments', 0) * 150} in SLA breach penalties while capturing ${round(sim_summary.get('projected_annual_savings', 0)/12000, 1)}K monthly savings."
        net_impact = f"Maintains target network SLA of {sla_summary.get('predicted_sla_compliance', 90.0)}% and utilizes under-capacity hubs for returns recycling."

        # Unified recommendations list
        recs = [
            "Initiate express lane transfers for high-priority shipments on congested corridors.",
            f"Reroute return shipments to {tpr1} during {hub2} congestion peaks.",
            f"Reallocate 3 drivers from stable routes to {best_route} corridor to handle volume spikes."
        ]

        return {
            "best_route": best_route,
            "lowest_cost_route": lowest_cost_route,
            "highest_sla_route": best_route,
            "confidence_score": confidence,
            "conflicts": conflicts,
            "business_impact": biz_impact,
            "network_impact": net_impact,
            "recommendations": recs,
            "avg_predicted_delay_hours": sla_summary.get("avg_predicted_delay_hours", 2.4),
            "refurbishment_recovery_usd": reverse_an.get("recovered_value", 5000.0)
        }
