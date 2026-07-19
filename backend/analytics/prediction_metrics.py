"""Prediction Metrics — Aggregates risk scores into summary statistics and chart payloads."""

from typing import Dict, Any, List


def compile_summary(shipments: List[Dict], hubs: List[Dict], corridors: List[Dict]) -> Dict[str, Any]:
    """Returns executive summary KPIs from risk-scored datasets."""
    if not shipments:
        return {
            "predicted_sla_compliance": 100.0,
            "high_risk_shipments": 0,
            "critical_hubs": 0,
            "upcoming_bottlenecks": 0,
            "avg_predicted_delay_hours": 0.0,
            "risk_distribution": {},
            "recovery_success_rate": 100.0
        }

    from collections import Counter
    levels = [s["risk_level"] for s in shipments]
    dist   = dict(Counter(levels))

    high_count     = dist.get("High", 0) + dist.get("Critical", 0)
    critical_hubs  = sum(1 for h in hubs if h["risk_level"] in ("High", "Critical"))
    bottlenecks    = sum(1 for c in corridors if c["risk_level"] in ("High", "Critical"))
    avg_delay      = round(sum(s["estimated_delay_hours"] for s in shipments) / len(shipments), 1)
    safe_count     = dist.get("Very Low", 0) + dist.get("Low", 0)
    compliance_pct = round((safe_count / len(shipments)) * 100.0, 1)
    recovery_rate  = round(100.0 - (high_count / len(shipments)) * 30.0, 1)

    return {
        "predicted_sla_compliance": compliance_pct,
        "high_risk_shipments": high_count,
        "critical_hubs": critical_hubs,
        "upcoming_bottlenecks": bottlenecks,
        "avg_predicted_delay_hours": avg_delay,
        "risk_distribution": dist,
        "recovery_success_rate": max(50.0, recovery_rate)
    }


def build_charts(shipments: List[Dict], hubs: List[Dict]) -> Dict[str, Any]:
    """Builds chart payload structures for Plotly rendering."""
    # Risk distribution pie
    from collections import Counter
    levels = [s["risk_level"] for s in shipments]
    dist = dict(Counter(levels))
    risk_pie = {
        "labels": list(dist.keys()),
        "values": list(dist.values()),
        "colors": ["#10b981", "#06b6d4", "#f59e0b", "#f97316", "#ef4444"]
    }

    # Hub risk bar
    hub_bar = {
        "hubs":   [h["hub"] for h in hubs],
        "scores": [h["risk_score"] for h in hubs],
        "colors": [h["risk_color"] for h in hubs]
    }

    # Delay forecast line (simulated future using breach probability trend)
    sorted_s = sorted(shipments, key=lambda x: x["breach_probability"], reverse=True)
    forecast_line = {
        "shipments": [s["transaction_id"] for s in sorted_s],
        "breach_probs": [s["breach_probability"] for s in sorted_s],
        "delays": [s["estimated_delay_hours"] for s in sorted_s]
    }

    return {
        "risk_distribution_pie": risk_pie,
        "hub_risk_bar": hub_bar,
        "delay_forecast_line": forecast_line
    }
