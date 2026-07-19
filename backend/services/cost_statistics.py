"""Stateless variance analysis calculator for shipment cost distributions."""

import numpy as np
import pandas as pd
from typing import Optional

from backend.models.cost_metrics import CostVarianceMetrics
from backend.utils.logger import logger


class CostStatistics:
    """Computes descriptive statistical measures for shipment cost distributions.
    
    This service is stateless and designed for dependency injection.
    All methods are class-level to allow direct invocation without instantiation.
    """

    @classmethod
    def compute_variance_metrics(cls, costs: pd.Series) -> CostVarianceMetrics:
        """Calculates variance analysis metrics from a series of shipment costs.
        
        Args:
            costs: Pandas Series of numeric shipment cost values.
            
        Returns:
            CostVarianceMetrics with max, min, median, std_dev, variance, Q1, Q3, IQR.
        """
        logger.info("CostStatistics: Computing variance metrics.")

        if costs is None or len(costs) == 0:
            logger.warning("CostStatistics: Empty cost series received. Returning zeroed metrics.")
            return CostVarianceMetrics(
                maximum=0.0, minimum=0.0, median=0.0,
                std_deviation=0.0, variance=0.0,
                q1=0.0, q3=0.0, iqr=0.0
            )

        # Drop NaN values for clean calculation
        clean_costs = costs.dropna().astype(float)

        if len(clean_costs) == 0:
            logger.warning("CostStatistics: All cost values are NaN. Returning zeroed metrics.")
            return CostVarianceMetrics(
                maximum=0.0, minimum=0.0, median=0.0,
                std_deviation=0.0, variance=0.0,
                q1=0.0, q3=0.0, iqr=0.0
            )

        maximum = float(clean_costs.max())
        minimum = float(clean_costs.min())
        median = float(clean_costs.median())
        std_deviation = float(clean_costs.std(ddof=1)) if len(clean_costs) > 1 else 0.0
        variance = float(clean_costs.var(ddof=1)) if len(clean_costs) > 1 else 0.0
        q1 = float(np.percentile(clean_costs, 25))
        q3 = float(np.percentile(clean_costs, 75))
        iqr = round(q3 - q1, 2)

        result = CostVarianceMetrics(
            maximum=round(maximum, 2),
            minimum=round(minimum, 2),
            median=round(median, 2),
            std_deviation=round(std_deviation, 2),
            variance=round(variance, 2),
            q1=round(q1, 2),
            q3=round(q3, 2),
            iqr=iqr
        )

        logger.info("CostStatistics: Statistics Generated event logged.")
        return result
