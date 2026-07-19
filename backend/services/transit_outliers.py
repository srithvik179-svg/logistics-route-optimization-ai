"""Transit time outlier detection using IQR-based statistical methods."""

import numpy as np
import pandas as pd
from typing import List

from backend.models.transit_metrics import TransitOutlier, TransitOutliers
from backend.utils.logger import logger


class TransitOutlierDetector:
    """Detects transit time outliers using IQR-based fence methodology.

    Classification:
        - Extremely Slow: transit_days > Q3 + 1.5 * IQR
        - Extremely Fast: transit_days < Q1 - 1.5 * IQR
        - Abnormal: transit_days > Q3 + 3.0 * IQR  (extreme outlier)
        - Long Delay Candidates: transit_days > median + 2 * std_deviation

    Stateless service for dependency injection.
    """

    @classmethod
    def detect_outliers(cls, df: pd.DataFrame, transit_col: str = "Transit_Days") -> TransitOutliers:
        """Detects transit time outliers from enriched transaction data.

        Args:
            df: DataFrame with transit_col, Transaction_ID, Origin_Hub, Destination_Hub.
            transit_col: Column name containing transit time in days.

        Returns:
            TransitOutliers with categorized outlier lists.
        """
        logger.info("TransitOutlierDetector: Scanning for transit outliers.")

        if df is None or len(df) == 0 or transit_col not in df.columns:
            logger.warning("TransitOutlierDetector: Insufficient data. Returning empty.")
            return TransitOutliers()

        clean = df.dropna(subset=[transit_col]).copy()
        if len(clean) == 0:
            return TransitOutliers()

        values = clean[transit_col].astype(float)
        q1 = float(np.percentile(values, 25))
        q3 = float(np.percentile(values, 75))
        iqr = q3 - q1
        median = float(values.median())
        std = float(values.std(ddof=1)) if len(values) > 1 else 0.0

        # Fences
        lower_fence = q1 - 1.5 * iqr
        upper_fence = q3 + 1.5 * iqr
        extreme_upper_fence = q3 + 3.0 * iqr
        long_delay_threshold = median + 2.0 * std

        extremely_slow: List[TransitOutlier] = []
        extremely_fast: List[TransitOutlier] = []
        abnormal: List[TransitOutlier] = []
        long_delay: List[TransitOutlier] = []

        for _, row in clean.iterrows():
            t = float(row[transit_col])
            tx_id = str(row.get("Transaction_ID", "N/A"))
            origin = str(row.get("Origin_Hub", "N/A"))
            dest = str(row.get("Destination_Hub", "N/A"))

            if iqr > 0:
                deviation = round(abs(t - median) / iqr, 2)
            else:
                deviation = 0.0

            outlier = TransitOutlier(
                transaction_id=tx_id,
                origin_hub=origin,
                destination_hub=dest,
                transit_days=round(t, 2),
                outlier_type="",
                deviation=deviation,
            )

            # Abnormal (extreme outlier — superset check first)
            if t > extreme_upper_fence:
                outlier.outlier_type = "abnormal"
                abnormal.append(outlier.model_copy())

            # Extremely Slow
            if t > upper_fence:
                outlier.outlier_type = "extremely_slow"
                extremely_slow.append(outlier.model_copy())

            # Extremely Fast
            if t < lower_fence:
                outlier.outlier_type = "extremely_fast"
                extremely_fast.append(outlier.model_copy())

            # Long Delay Candidate
            if std > 0 and t > long_delay_threshold:
                outlier.outlier_type = "long_delay"
                long_delay.append(outlier.model_copy())

        total = len(set(
            [o.transaction_id for o in extremely_slow] +
            [o.transaction_id for o in extremely_fast] +
            [o.transaction_id for o in abnormal] +
            [o.transaction_id for o in long_delay]
        ))

        logger.info(f"TransitOutlierDetector: Outliers Detected event logged. Total unique: {total}")

        return TransitOutliers(
            extremely_slow=extremely_slow,
            extremely_fast=extremely_fast,
            abnormal=abnormal,
            long_delay_candidates=long_delay,
            total_outliers=total,
        )
