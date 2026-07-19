"""Stateless descriptive statistics calculator for transit time distributions."""

import numpy as np
import pandas as pd
from typing import Dict, Any

from backend.utils.logger import logger


class TransitStatistics:
    """Computes descriptive statistical measures for transit time distributions.

    Stateless service with class-level methods for dependency injection.
    """

    @classmethod
    def compute_stats(cls, transit_days: pd.Series) -> Dict[str, float]:
        """Calculates variance analysis metrics from a series of transit days.

        Args:
            transit_days: Pandas Series of numeric transit time values (in days).

        Returns:
            Dict with keys: avg, median, min, max, std_deviation, variance.
        """
        logger.info("TransitStatistics: Computing transit time statistics.")

        zeros = {
            "avg": 0.0, "median": 0.0, "min": 0.0, "max": 0.0,
            "std_deviation": 0.0, "variance": 0.0,
        }

        if transit_days is None or len(transit_days) == 0:
            logger.warning("TransitStatistics: Empty series received. Returning zeroed metrics.")
            return zeros

        clean = transit_days.dropna().astype(float)
        if len(clean) == 0:
            logger.warning("TransitStatistics: All values are NaN. Returning zeroed metrics.")
            return zeros

        result = {
            "avg": round(float(clean.mean()), 2),
            "median": round(float(clean.median()), 2),
            "min": round(float(clean.min()), 2),
            "max": round(float(clean.max()), 2),
            "std_deviation": round(float(clean.std(ddof=1)), 2) if len(clean) > 1 else 0.0,
            "variance": round(float(clean.var(ddof=1)), 2) if len(clean) > 1 else 0.0,
        }

        logger.info("TransitStatistics: Transit Metrics Generated event logged.")
        return result
