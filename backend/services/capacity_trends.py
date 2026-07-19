"""Time-series trend dataset generator for logistics capacity analysis."""

import pandas as pd
from typing import List, Dict, Any
from backend.models.capacity_metrics import CapacityTrends, CapacityTrendPoint
from backend.utils.logger import logger


class CapacityTrendsService:
    """Generates daily, weekly, monthly, and quarterly capacity trend points.

    Stateless service designed for reusability.
    """

    @classmethod
    def generate_trends(
        cls,
        tx_df: pd.DataFrame,
        total_capacity: float
    ) -> CapacityTrends:
        """Aggregates capacity levels and utilization trends.

        Args:
            tx_df: Transactions DataFrame.
            total_capacity: Total network capacity limit.

        Returns:
            CapacityTrends containing chronological performance datasets.
        """
        logger.info("CapacityTrendsService: Generating capacity trend datasets.")

        trends = CapacityTrends()

        if tx_df is None or len(tx_df) == 0:
            logger.warning("CapacityTrendsService: Empty data. Returning empty trends.")
            return trends

        # Setup datetime indexing
        df_tx = tx_df.copy()
        df_tx["Order_Date"] = pd.to_datetime(df_tx["Order_Date"], errors="coerce")
        df_tx = df_tx.dropna(subset=["Order_Date", "Quantity"])

        if len(df_tx) == 0:
            return trends

        df_tx = df_tx.sort_values("Order_Date")

        trends.daily = cls._aggregate_trend(df_tx, total_capacity, freq="D", fmt="%Y-%m-%d")
        trends.weekly = cls._aggregate_trend(df_tx, total_capacity, freq="W", fmt="%Y-W%U")
        trends.monthly = cls._aggregate_trend(df_tx, total_capacity, freq="MS", fmt="%Y-%m")
        trends.quarterly = cls._aggregate_trend(df_tx, total_capacity, freq="QS", fmt="Q")

        logger.info("CapacityTrendsService: Capacity Trends Generated.")
        return trends

    @classmethod
    def _aggregate_trend(
        cls,
        tx_df: pd.DataFrame,
        total_capacity: float,
        freq: str,
        fmt: str
    ) -> List[CapacityTrendPoint]:
        points: List[CapacityTrendPoint] = []

        # resample transactions to get chronological usage
        # Since transactions are flows, we can use quantity as a proxy for utilized capacity in that period
        # Resampled quantity represents used capacity in the time bucket
        usage_resampled = tx_df.set_index("Order_Date").resample(freq)["Quantity"].sum()

        for period, used_val in usage_resampled.items():
            if freq == "QS":
                quarter_num = (period.month - 1) // 3 + 1
                label = f"{period.year}-Q{quarter_num}"
            else:
                label = period.strftime(fmt)

            used = round(float(used_val), 2)
            # Clip used capacity at total_capacity limit to avoid >100% physically impossible values
            used = min(used, total_capacity)

            avail = total_capacity - used
            avail_rate = (avail / total_capacity) * 100.0 if total_capacity > 0 else 100.0

            points.append(CapacityTrendPoint(
                period=label,
                total_capacity=round(total_capacity, 2),
                used_capacity=used,
                availability_rate=round(avail_rate, 1)
            ))

        return points
