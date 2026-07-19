"""Time-series trend dataset generator for logistics inventory analysis."""

import pandas as pd
from typing import List, Dict, Any
from backend.models.inventory_metrics import InventoryTrends, InventoryTrendPoint
from backend.utils.logger import logger


class InventoryTrendsService:
    """Generates daily, weekly, monthly, and quarterly inventory trend points.

    Stateless service designed for reusability and dependency injection.
    """

    @classmethod
    def generate_trends(
        cls,
        tx_df: pd.DataFrame,
        stock_history: List[Dict[str, Any]]
    ) -> InventoryTrends:
        """Aggregates inventory trends across daily, weekly, monthly, and quarterly timeframes.

        Args:
            tx_df: Transactions DataFrame.
            stock_history: List of historical stock state records, each containing
                           {'date': datetime, 'avg_stock': float}.

        Returns:
            InventoryTrends containing temporal performance lists.
        """
        logger.info("InventoryTrendsService: Generating time-series trends.")

        trends = InventoryTrends()

        if tx_df is None or len(tx_df) == 0:
            logger.warning("InventoryTrendsService: Empty data. Returning empty trends.")
            return trends

        # Setup datetime indexing
        df_tx = tx_df.copy()
        df_tx["Order_Date"] = pd.to_datetime(df_tx["Order_Date"], errors="coerce")
        df_tx = df_tx.dropna(subset=["Order_Date", "Quantity"])

        if len(df_tx) == 0:
            return trends

        df_tx = df_tx.sort_values("Order_Date")

        # Convert stock_history to a DataFrame
        history_df = pd.DataFrame(stock_history)
        if len(history_df) > 0:
            history_df["date"] = pd.to_datetime(history_df["date"])
            history_df = history_df.sort_values("date")

        # Generate each frequency
        trends.daily = cls._aggregate_trend(df_tx, history_df, freq="D", fmt="%Y-%m-%d")
        trends.weekly = cls._aggregate_trend(df_tx, history_df, freq="W", fmt="%Y-W%U")
        trends.monthly = cls._aggregate_trend(df_tx, history_df, freq="MS", fmt="%Y-%m")
        trends.quarterly = cls._aggregate_trend(df_tx, history_df, freq="QS", fmt="Q")

        logger.info("InventoryTrendsService: Inventory Trends Generated.")
        return trends

    @classmethod
    def _aggregate_trend(
        cls,
        tx_df: pd.DataFrame,
        history_df: pd.DataFrame,
        freq: str,
        fmt: str
    ) -> List[InventoryTrendPoint]:
        """Helper to resample and aggregate transaction movements and average stock level."""
        points: List[InventoryTrendPoint] = []

        # resample transactions
        incoming_resampled = tx_df.set_index("Order_Date").resample(freq)["Quantity"].sum()
        
        # Outgoing total (where destination is not a hub, or we can just count total transactions as flow)
        # Actually, let's look at Origin_Hub vs Destination_Hub
        # Since transactions represent movement from origin to destination, incoming = sum(quantity) at dest,
        # outgoing = sum(quantity) at origin.
        # Across the whole network, total incoming = total outgoing = total sum of quantities.
        # So we can resample total units moved.
        total_moved = incoming_resampled

        # resample stock history
        history_resampled = None
        if history_df is not None and len(history_df) > 0:
            history_resampled = history_df.set_index("date").resample(freq)["avg_stock"].mean()

        for period, incoming_val in total_moved.items():
            # Build label
            if freq == "QS":
                quarter_num = (period.month - 1) // 3 + 1
                label = f"{period.year}-Q{quarter_num}"
            else:
                label = period.strftime(fmt)

            # Average stock level in this period
            avg_stock = 100.0  # nominal default baseline stock
            if history_resampled is not None and period in history_resampled.index:
                val = history_resampled[period]
                if pd.notna(val):
                    avg_stock = float(val)

            points.append(InventoryTrendPoint(
                period=label,
                avg_stock_level=round(avg_stock, 2),
                incoming_units=round(float(incoming_val), 2),
                outgoing_units=round(float(incoming_val), 2)  # Balanced flow
            ))

        return points
