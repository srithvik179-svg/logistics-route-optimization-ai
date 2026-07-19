"""Anomaly and outlier detection for inventory transaction spikes, drops, overstock, and understock."""

import numpy as np
import pandas as pd
from typing import List, Dict, Any
from backend.models.inventory_metrics import InventoryAnomaly, InventoryOutliers
from backend.utils.logger import logger


class InventoryOutlierDetector:
    """Detects inventory transaction spikes, drops, abnormal levels, and overstock/understock positions.

    Stateless service designed for dependency injection.
    """

    @classmethod
    def detect_anomalies(
        cls,
        stock_df: pd.DataFrame,
        tx_df: pd.DataFrame,
        capacities: Dict[str, float],
        critical_threshold: float = 15.0,
        overstock_threshold_pct: float = 90.0
    ) -> InventoryOutliers:
        """Runs outlier detection rules across inventory stock levels and daily transactions.

        Args:
            stock_df: DataFrame with 'location', 'part_number', 'stock_level'.
            tx_df: Transactions DataFrame.
            capacities: Dict mapping location ID to storage capacity.
            critical_threshold: Stock level below which an item is considered understocked.
            overstock_threshold_pct: Percentage of capacity above which a node is overstocked.

        Returns:
            InventoryOutliers payload containing categorized anomaly lists.
        """
        logger.info("InventoryOutlierDetector: Running anomaly detection.")

        outliers = InventoryOutliers()

        if stock_df is None or len(stock_df) == 0:
            return outliers

        # 1. Abnormal stock levels (IQR-based on overall location-part stock levels)
        levels = stock_df["stock_level"].astype(float)
        if len(levels) > 4:
            q1 = float(np.percentile(levels, 25))
            q3 = float(np.percentile(levels, 75))
            iqr = q3 - q1
            median = float(levels.median())
            
            upper_fence = q3 + 1.5 * iqr
            lower_fence = q1 - 1.5 * iqr

            for _, row in stock_df.iterrows():
                lvl = float(row["stock_level"])
                loc = str(row["location"])
                part = str(row["part_number"])

                if lvl > upper_fence or lvl < lower_fence:
                    dev = round(abs(lvl - median) / iqr, 2) if iqr > 0 else 0.0
                    outliers.abnormal_levels.append(InventoryAnomaly(
                        location=loc,
                        part_number=part,
                        metric_value=lvl,
                        anomaly_type="abnormal",
                        description=f"Stock level {lvl} is abnormal. Median is {median} (IQR={iqr}, Dev={dev})"
                    ))

        # 2. Overstock / Understock checks
        # Aggregate current stock level by location
        loc_stock = stock_df.groupby("location")["stock_level"].sum().reset_index()
        for _, row in loc_stock.iterrows():
            loc = str(row["location"])
            total_stock = float(row["stock_level"])
            cap = capacities.get(loc, 1000.0)  # Default capacity is 1000.0 if not specified
            occupancy = (total_stock / cap) * 100.0

            if occupancy >= overstock_threshold_pct:
                outliers.potential_overstock.append(InventoryAnomaly(
                    location=loc,
                    metric_value=round(occupancy, 1),
                    anomaly_type="overstock",
                    description=f"Location {loc} overstocked at {occupancy:.1f}% capacity ({total_stock:.1f}/{cap:.1f} units)"
                ))
            
            if total_stock < critical_threshold:
                outliers.potential_understock.append(InventoryAnomaly(
                    location=loc,
                    metric_value=total_stock,
                    anomaly_type="understock",
                    description=f"Location {loc} understocked. Total stock is {total_stock:.1f} units (Threshold={critical_threshold})"
                ))

        # 3. Transaction Spikes and Drops
        if tx_df is not None and len(tx_df) > 0 and "Order_Date" in tx_df.columns:
            # Aggregate daily incoming transaction quantities
            daily_in = tx_df.groupby("Order_Date")["Quantity"].sum().reset_index()
            daily_in.columns = ["Order_Date", "qty"]

            qtys = daily_in["qty"].astype(float)
            if len(qtys) > 4:
                q1 = float(np.percentile(qtys, 25))
                q3 = float(np.percentile(qtys, 75))
                iqr = q3 - q1
                median = float(qtys.median())

                upper_fence = q3 + 1.5 * iqr
                lower_fence = q1 - 1.5 * iqr

                for _, row in daily_in.iterrows():
                    dt = str(row["Order_Date"])
                    qty = float(row["qty"])

                    if qty > upper_fence:
                        outliers.spikes.append(InventoryAnomaly(
                            location=dt,  # using Date as identifier for temporal outlier
                            metric_value=qty,
                            anomaly_type="spike",
                            description=f"Daily incoming units spike on {dt}: {qty} units (Median={median})"
                        ))
                    elif qty < lower_fence:
                        outliers.drops.append(InventoryAnomaly(
                            location=dt,
                            metric_value=qty,
                            anomaly_type="drop",
                            description=f"Daily incoming units drop on {dt}: {qty} units (Median={median})"
                        ))

        # Unique count of anomalies
        total = (
            len(outliers.spikes) +
            len(outliers.drops) +
            len(outliers.abnormal_levels) +
            len(outliers.potential_overstock) +
            len(outliers.potential_understock)
        )
        outliers.total_anomalies = total

        logger.info(f"InventoryOutlierDetector: Outliers Generated. Total unique: {total}")
        return outliers
