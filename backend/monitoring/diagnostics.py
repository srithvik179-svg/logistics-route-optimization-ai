"""Diagnostics service aggregating traces and logs to produce diagnostic summaries."""

import uuid
import time
from typing import List, Dict, Any
from backend.models.diagnostic_report import DiagnosticReport
from backend.monitoring.metrics_collector import MetricsCollector


class DiagnosticsService:
    """Consolidates system analytics metrics to output health and run diagnostic reports."""

    @classmethod
    def generate_report(cls) -> DiagnosticReport:
        """Analyzes collector telemetry to package a DiagnosticReport.

        Returns:
            DiagnosticReport model.
        """
        metrics = MetricsCollector.get_snapshot_data()

        # 1. Determine performance summary descriptions
        err_rate = metrics["error_rate"]
        avg_time = metrics["api_response_time_avg"]

        if err_rate > 0.05:
            summary = "DEGRADED: System is experiencing elevated request failure rates."
        elif avg_time > 500.0:
            summary = "WARNING: Average response latencies exceed standard threshold (500ms)."
        else:
            summary = "OPTIMAL: All monitored routes operate within healthy performance bounds."

        # 2. Extract slowest services
        traces = metrics["traces"]
        slow_services = []
        if traces:
            # Group by service name and average execution times
            svc_times: Dict[str, List[float]] = {}
            for t in traces:
                svc_times.setdefault(t.service_name, []).append(t.execution_time_ms)
            
            svc_avgs = {name: (sum(times)/len(times)) for name, times in svc_times.items()}
            # Sort descending
            sorted_svcs = sorted(svc_avgs.items(), key=lambda x: x[1], reverse=True)
            slow_services = [f"{name} ({avg:.1f}ms)" for name, avg in sorted_svcs[:5]]

        # 3. Extract most requested APIs
        path_counts = metrics["path_counts"]
        sorted_paths = sorted(path_counts.items(), key=lambda x: x[1], reverse=True)
        most_requested = [f"{path} ({count} calls)" for path, count in sorted_paths[:5]]

        # 4. Error analysis
        failure_analysis = {
            "failed_requests_total": metrics["failed_requests"],
            "error_counts_by_status": metrics["error_counts"]
        }

        # 5. Compile exceptions
        recent_exceptions = metrics["exceptions"]

        report = DiagnosticReport(
            report_id=str(uuid.uuid4()),
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            performance_summary=summary,
            slowest_services=slow_services,
            most_requested_apis=most_requested,
            failure_analysis=failure_analysis,
            recent_exceptions=recent_exceptions
        )

        return report
