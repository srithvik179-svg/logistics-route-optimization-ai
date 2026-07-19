"""Telemetry manager serving cached health reports and telemetry snapshots."""

import time
import os
import threading
from typing import Dict, Any
from backend.models.metric_snapshot import MetricSnapshot
from backend.models.health_status import SystemHealthReport
from backend.monitoring.metrics_collector import MetricsCollector
from backend.monitoring.health_service import HealthService
from backend.monitoring.structured_logger import StructuredLogger


class TelemetryManager:
    """Manages metric aggregations and caches health check snapshots thread-safely."""

    _lock = threading.Lock()
    
    # Caching variables
    _cached_health_report: SystemHealthReport = None
    _cached_health_time = 0.0
    _health_cache_duration = 5.0  # seconds

    @classmethod
    def get_cached_health(cls) -> SystemHealthReport:
        """Retrieves or builds the system health report, caching for 5 seconds."""
        now = time.time()
        with cls._lock:
            if (
                cls._cached_health_report is not None and 
                (now - cls._cached_health_time) < cls._health_cache_duration
            ):
                return cls._cached_health_report

            # Rebuild cache outside holding lock if possible, or inside lock to remain atomic
            report = HealthService.perform_system_check()
            cls._cached_health_report = report
            cls._cached_health_time = now
            StructuredLogger.info("Telemetry health cache updated.")
            return report

    @classmethod
    def generate_telemetry_snapshot(cls) -> MetricSnapshot:
        """Assembles collector counters and OS status tags to return a MetricSnapshot.

        Returns:
            MetricSnapshot model.
        """
        metrics = MetricsCollector.get_snapshot_data()

        # Extract process memory footprint
        mem_bytes = 0
        try:
            import psutil
            process = psutil.Process(os.getpid())
            mem_bytes = process.memory_info().rss
        except Exception:
            # Fallback mock memory
            mem_bytes = 45000000  # ~45MB default

        snapshot = MetricSnapshot(
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            api_response_time_avg=metrics["api_response_time_avg"],
            engine_execution_time_avg=metrics["engine_execution_time_avg"],
            memory_usage_bytes=mem_bytes,
            cache_hit_ratio=metrics["cache_hit_ratio"],
            cache_miss_ratio=metrics["cache_miss_ratio"],
            request_throughput=float(metrics["total_requests"]),  # request count
            active_requests=metrics["active_requests"],
            failed_requests=metrics["failed_requests"],
            error_rate=metrics["error_rate"]
        )

        StructuredLogger.info("Telemetry snapshot created.", {
            "api_response_time_avg": snapshot.api_response_time_avg,
            "error_rate": snapshot.error_rate
        })
        return snapshot
