"""Time-series trend dataset generator for SLA compliance analysis."""

import pandas as pd
from typing import List, Dict, Any
from backend.models.sla_metrics import SLATrends, SLATrendPoint
from backend.utils.logger import logger


class SLATrendsService:
    """Generates daily, weekly, monthly, and quarterly SLA trend points.

    Stateless service designed for reusability.
    """

    @classmethod
    def generate_trends(
        cls,
        tx_df: pd.DataFrame,
        transit_limit: float = 3.0
    ) -> SLATrends:
        """Aggregates transaction compliance over daily, weekly, monthly, and quarterly buckets.

        Args:
            tx_df: Enriched transactions DataFrame.
            transit_limit: Configure SLA transit limit.

        Returns:
            SLATrends containing chronological trend lines.
        """
        logger.info("SLATrendsService: Generating SLA trend datasets.")

        trends = SLATrends()

        if tx_df is None or len(tx_df) == 0:
            logger.warning("SLATrendsService: Empty data. Returning empty trends.")
            return trends

        # Setup datetime indexing
        df_tx = tx_df.copy()
        df_tx["Order_Date"] = pd.to_datetime(df_tx["Order_Date"], errors="coerce")
        df_tx = df_tx.dropna(subset=["Order_Date", "Transit_Days"])

        if len(df_tx) == 0:
            return trends

        df_tx = df_tx.sort_values("Order_Date")

        trends.daily = cls._aggregate_trend(df_tx, transit_limit, freq="D", fmt="%Y-%m-%d")
        trends.weekly = cls._aggregate_trend(df_tx, transit_limit, freq="W", fmt="%Y-W%U")
        trends.monthly = cls._aggregate_trend(df_tx, transit_limit, freq="MS", fmt="%Y-%m")
        trends.quarterly = cls._aggregate_trend(df_tx, transit_limit, freq="QS", fmt="Q")

        logger.info("SLATrendsService: Trend Datasets Generated.")
        return trends

    @classmethod
    def _aggregate_trend(
        cls,
        tx_df: pd.DataFrame,
        transit_limit: float,
        freq: str,
        fmt: str
    ) -> List[SLATrendPoint]:
        points: List[SLATrendPoint] = []

        # resample transactions to get chronological usage
        grouped = tx_df.set_index("Order_Date").resample(freq)

        for period, group in grouped:
            if len(group) == 0:
                continue

            if freq == "QS":
                quarter_num = (period.month - 1) // 3 + 1
                label = f"{period.year}-Q{quarter_num}"
            else:
                label = period.strftime(fmt)

            total = len(group)
            met_count = int((group["Transit_Days"] <= transit_limit).sum())
            violations = total - met_count
            compliance = (met_count / total) * 100.0 if total > 0 else 100.0

            points.append(SLATrendPoint(
                period=label,
                compliance_pct=round(compliance, 1),
                total_shipments=total,
                violation_count=violations
            ))

        return points
