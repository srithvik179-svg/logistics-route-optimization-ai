"""Bottleneck detection for overloaded, underutilized, saturated, or imbalanced network resources."""

import numpy as np
from typing import List
from backend.models.capacity_metrics import CapacityBottlenecks, BottleneckAnomaly, NodeCapacityMetrics
from backend.utils.logger import logger


class CapacityBottleneckDetector:
    """Detects capacity bottlenecks in the logistics network using threshold rules and statistical metrics.

    Stateless service designed for reusability.
    """

    @classmethod
    def detect_bottlenecks(
        cls,
        hubs_analysis: List[NodeCapacityMetrics],
        rcs_analysis: List[NodeCapacityMetrics]
    ) -> CapacityBottlenecks:
        """Evaluates utilization rates to detect anomalies, saturation, and imbalances.

        Args:
            hubs_analysis: Detailed hub capacity metrics list.
            rcs_analysis: Detailed repair center capacity metrics list.

        Returns:
            CapacityBottlenecks payload container.
        """
        logger.info("CapacityBottleneckDetector: Analyzing network bottlenecks.")

        bottlenecks = CapacityBottlenecks()

        # Check overloaded and underutilized hubs
        for h in hubs_analysis:
            if h.utilization_pct > 90.0:
                bottlenecks.overloaded_hubs.append(BottleneckAnomaly(
                    entity_id=h.node_id,
                    utilization_pct=h.utilization_pct,
                    anomaly_type="overloaded_hub",
                    description=f"Hub {h.node_id} is overloaded ({h.utilization_pct:.1f}% utilization). Limit exceeded."
                ))
            elif h.utilization_pct < 20.0:
                bottlenecks.underutilized_hubs.append(BottleneckAnomaly(
                    entity_id=h.node_id,
                    utilization_pct=h.utilization_pct,
                    anomaly_type="underutilized_hub",
                    description=f"Hub {h.node_id} is underutilized ({h.utilization_pct:.1f}% utilization). Over-provisioned."
                ))

        # Check overloaded and idle repair centers
        for rc in rcs_analysis:
            if rc.utilization_pct > 90.0:
                bottlenecks.overloaded_repair_centers.append(BottleneckAnomaly(
                    entity_id=rc.node_id,
                    utilization_pct=rc.utilization_pct,
                    anomaly_type="overloaded_rc",
                    description=f"Repair Center {rc.node_id} is overloaded ({rc.utilization_pct:.1f}% utilization). High delay risk."
                ))
            elif rc.utilization_pct < 15.0:
                bottlenecks.idle_repair_centers.append(BottleneckAnomaly(
                    entity_id=rc.node_id,
                    utilization_pct=rc.utilization_pct,
                    anomaly_type="idle_rc",
                    description=f"Repair Center {rc.node_id} is idle ({rc.utilization_pct:.1f}% utilization). Resource wasted."
                ))

        # Capacity saturation check (weighted network utilization)
        total_cap = sum(n.capacity for n in hubs_analysis + rcs_analysis)
        used_cap = sum(n.used_capacity for n in hubs_analysis + rcs_analysis)
        network_util = (used_cap / total_cap) * 100.0 if total_cap > 0 else 0.0

        if network_util > 85.0:
            bottlenecks.capacity_saturation_flag = True
            logger.warning("CapacityBottleneckDetector: Network capacity saturation detected!")

        # Capacity imbalance check (standard deviation of utilization rates > 25.0)
        utils = [n.utilization_pct for n in hubs_analysis + rcs_analysis]
        if len(utils) > 1:
            std_dev = float(np.std(utils))
            if std_dev > 25.0:
                bottlenecks.capacity_imbalance_flag = True
                logger.warning(f"CapacityBottleneckDetector: Network capacity imbalance detected (std_dev={std_dev:.2f}).")

        # Aggregate unique counts
        total = (
            len(bottlenecks.overloaded_hubs) +
            len(bottlenecks.underutilized_hubs) +
            len(bottlenecks.overloaded_repair_centers) +
            len(bottlenecks.idle_repair_centers)
        )
        bottlenecks.total_bottlenecks = total

        logger.info(f"CapacityBottleneckDetector: Bottlenecks Generated. Total count: {total}")
        return bottlenecks
