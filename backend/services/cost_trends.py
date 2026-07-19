"""Time-series trend dataset generator for logistics cost analysis."""

import pandas as pd
from typing import Dict, List, Any

from backend.models.cost_metrics import CostTrendPoint, CostTrends
from backend.utils.logger import logger


class CostTrendsService:
    """Generates reusable time-series cost datasets at daily, weekly, monthly, and quarterly granularity.
    
    These datasets are designed to be consumed by future prediction models and dashboard charts.
    """

    @classmethod
    def generate_trends(cls, df: pd.DataFrame) -> CostTrends:
        """Aggregates shipment costs into daily, weekly, monthly, and quarterly time buckets.
        
        Args:
            df: Enriched transactions DataFrame with Order_Date and Shipment_Cost columns.
            
        Returns:
            CostTrends containing four lists of CostTrendPoint.
        """
        logger.info("CostTrendsService: Generating time-series trend datasets.")

        if df is None or len(df) == 0:
            logger.warning("CostTrendsService: Empty DataFrame. Returning empty trends.")
            return CostTrends()

        if "Order_Date" not in df.columns or "Shipment_Cost" not in df.columns:
            logger.warning("CostTrendsService: Missing required columns (Order_Date, Shipment_Cost). Skipping.")
            return CostTrends()

        # Ensure datetime type
        df_work = df.copy()
        df_work["Order_Date"] = pd.to_datetime(df_work["Order_Date"], errors="coerce")
        df_work = df_work.dropna(subset=["Order_Date", "Shipment_Cost"])

        if len(df_work) == 0:
            logger.warning("CostTrendsService: No valid date/cost rows after cleaning. Returning empty.")
            return CostTrends()

        df_work = df_work.sort_values("Order_Date")

        trends = CostTrends()

        # --- Daily Aggregation ---
        trends.daily = cls._aggregate_by_period(df_work, freq="D", label_format="%Y-%m-%d")

        # --- Weekly Aggregation ---
        trends.weekly = cls._aggregate_by_period(df_work, freq="W", label_format="%Y-W%U")

        # --- Monthly Aggregation ---
        trends.monthly = cls._aggregate_by_period(df_work, freq="MS", label_format="%Y-%m")

        # --- Quarterly Aggregation ---
        trends.quarterly = cls._aggregate_by_period(df_work, freq="QS", label_format="%Y-Q")

        logger.info("CostTrendsService: Trend Dataset Generated event logged.")
        return trends

    @classmethod
    def _aggregate_by_period(
        cls,
        df: pd.DataFrame,
        freq: str,
        label_format: str
    ) -> List[CostTrendPoint]:
        """Aggregates cost data by a pandas frequency string.
        
        Args:
            df: Working DataFrame with Order_Date (datetime) and Shipment_Cost columns.
            freq: Pandas offset alias (D, W, MS, QS).
            label_format: strftime format for the period label.
            
        Returns:
            List of CostTrendPoint sorted chronologically.
        """
        grouped = df.set_index("Order_Date").resample(freq)["Shipment_Cost"]

        points: List[CostTrendPoint] = []
        for period, group in grouped:
            if len(group) == 0:
                continue

            # Build period label
            if freq == "QS":
                quarter_num = (period.month - 1) // 3 + 1
                label = f"{period.year}-Q{quarter_num}"
            else:
                label = period.strftime(label_format)

            points.append(CostTrendPoint(
                period=label,
                total_cost=round(float(group.sum()), 2),
                avg_cost=round(float(group.mean()), 2),
                shipment_count=int(group.count())
            ))

        return points
