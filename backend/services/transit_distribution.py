"""Transit time distribution, frequency, histogram, and category generator."""

import pandas as pd
import numpy as np
from typing import List, Dict

from backend.models.transit_metrics import (
    TransitDistribution,
    TransitDistributionBucket,
    TransitCategory,
)
from backend.utils.logger import logger


class TransitDistributionService:
    """Generates transit time distribution analysis including histograms, frequency maps, and speed categories.

    Stateless service designed for reusability and dependency injection.
    """

    # Category thresholds (in days)
    FAST_MAX = 1.0
    NORMAL_MAX = 3.0
    SLOW_MAX = 5.0
    # Anything above SLOW_MAX is Critical Delay

    @classmethod
    def generate_distribution(cls, transit_days: pd.Series) -> TransitDistribution:
        """Generates histogram, frequency map, and speed categories from transit times.

        Args:
            transit_days: Pandas Series of transit time values in days.

        Returns:
            TransitDistribution with histogram, categories, and frequency map.
        """
        logger.info("TransitDistributionService: Generating transit distribution.")

        if transit_days is None or len(transit_days) == 0:
            logger.warning("TransitDistributionService: Empty series. Returning empty distribution.")
            return TransitDistribution()

        clean = transit_days.dropna().astype(float)
        if len(clean) == 0:
            return TransitDistribution()

        total = len(clean)

        # --- Histogram Buckets ---
        histogram = cls._build_histogram(clean, total)

        # --- Frequency Map ---
        frequency: Dict[int, int] = {}
        for val in clean:
            day_int = int(round(val))
            frequency[day_int] = frequency.get(day_int, 0) + 1

        # --- Speed Categories ---
        categories = cls._build_categories(clean, total)

        logger.info("TransitDistributionService: Transit Distribution Generated event logged.")
        return TransitDistribution(
            histogram=histogram,
            categories=categories,
            frequency=frequency,
        )

    @classmethod
    def _build_histogram(cls, clean: pd.Series, total: int) -> List[TransitDistributionBucket]:
        """Builds histogram buckets for transit time distribution."""
        min_val = float(clean.min())
        max_val = float(clean.max())

        # Create sensible buckets
        if max_val <= min_val:
            return [TransitDistributionBucket(
                bucket_label=f"{min_val:.0f} days",
                count=total,
                percentage=100.0,
            )]

        # Use 1-day buckets for small ranges, otherwise auto-bin
        range_span = max_val - min_val
        if range_span <= 10:
            edges = list(range(int(min_val), int(max_val) + 2))
        else:
            edges = list(np.linspace(min_val, max_val + 0.01, min(11, total + 1)))

        buckets: List[TransitDistributionBucket] = []
        for i in range(len(edges) - 1):
            lo, hi = edges[i], edges[i + 1]
            count = int(((clean >= lo) & (clean < hi)).sum())
            # Include the upper bound in the last bucket
            if i == len(edges) - 2:
                count = int(((clean >= lo) & (clean <= hi)).sum())

            pct = round((count / total) * 100, 1) if total > 0 else 0.0
            label = f"{lo:.0f}-{hi:.0f} days"
            buckets.append(TransitDistributionBucket(
                bucket_label=label,
                count=count,
                percentage=pct,
            ))

        return buckets

    @classmethod
    def _build_categories(cls, clean: pd.Series, total: int) -> List[TransitCategory]:
        """Classifies shipments into speed categories."""
        categories_def = [
            ("Fast", 0, cls.FAST_MAX),
            ("Normal", cls.FAST_MAX, cls.NORMAL_MAX),
            ("Slow", cls.NORMAL_MAX, cls.SLOW_MAX),
            ("Critical Delay", cls.SLOW_MAX, float("inf")),
        ]

        categories: List[TransitCategory] = []
        for name, lo, hi in categories_def:
            if hi == float("inf"):
                mask = clean > lo
            else:
                mask = (clean > lo) & (clean <= hi)

            # Special case for Fast: include 0 and up to threshold
            if name == "Fast":
                mask = clean <= cls.FAST_MAX

            subset = clean[mask]
            count = int(len(subset))
            pct = round((count / total) * 100, 1) if total > 0 else 0.0
            avg_t = round(float(subset.mean()), 2) if count > 0 else 0.0

            categories.append(TransitCategory(
                category=name,
                count=count,
                percentage=pct,
                avg_transit_time=avg_t,
            ))

        return categories
