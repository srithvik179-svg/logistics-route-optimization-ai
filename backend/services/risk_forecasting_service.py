"""Risk Forecasting Service — Time-series risk trend projection and corridor future forecasts."""

from typing import Dict, Any, List
import datetime
from backend.services.repository import repository
from backend.analytics.risk_engine import score_hubs, score_corridors, _risk_level
from backend.utils.logger import logger


class RiskForecastingService:
    """Projects risk trends over the next 7 days using historical SLA miss patterns."""

    @classmethod
    def get_forecast_payload(cls, filters: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("RiskForecastingService: Building 7-day risk forecast payload.")

        import pandas as pd
        df = repository._processed_sheets.get("Logistics_Transactions")
        if df is None or df.empty:
            return {"timeline": [], "corridor_forecast": [], "peak_day": "N/A"}

        # Build synthetic 7-day rolling risk forecast
        today = datetime.date.today()
        missed_total = len(df[df["SLA_Status"] == "MISSED"])
        total = len(df)
        base_miss_rate = (missed_total / max(1, total)) * 100.0

        timeline = []
        for i in range(7):
            day = today + datetime.timedelta(days=i)
            # Add cyclical variance (weekends slightly lower, mid-week peaks)
            weekday = day.weekday()
            variance = [0.0, 5.0, 8.0, 12.0, 6.0, -5.0, -8.0][weekday]
            projected_rate = max(0.0, min(100.0, base_miss_rate + variance))
            level = _risk_level(projected_rate)
            timeline.append({
                "date": day.isoformat(),
                "day_name": day.strftime("%a"),
                "projected_miss_rate": round(projected_rate, 1),
                "risk_level": level,
                "predicted_delays": round(projected_rate * 0.3, 1),
                "shipments_at_risk": max(0, int(projected_rate * 0.1))
            })

        peak_day = max(timeline, key=lambda x: x["projected_miss_rate"])["day_name"]
        corridors = score_corridors(df)

        return {
            "timeline": timeline,
            "corridor_forecast": corridors[:5],
            "peak_day": peak_day,
            "base_miss_rate": round(base_miss_rate, 1)
        }
