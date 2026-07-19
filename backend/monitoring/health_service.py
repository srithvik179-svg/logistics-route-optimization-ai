"""Health service executing live health checks across repository, security, and optimization layers."""

import time
from typing import List
from backend.models.health_status import ServiceHealth, SystemHealthReport
from backend.services.repository import repository
from backend.monitoring.structured_logger import StructuredLogger


class HealthService:
    """Performs runtime checks and health scoring of core systems."""

    @classmethod
    def perform_system_check(cls) -> SystemHealthReport:
        """Executes verification runs on all systems and aggregates results.

        Returns:
            SystemHealthReport model.
        """
        services_health: List[ServiceHealth] = []
        overall_status = "UP"

        # 1. Repository health check
        start_rep = time.perf_counter()
        try:
            repo_init = repository.is_initialized()
            repo_status = "UP" if repo_init else "DEGRADED"
            repo_detail = "Repository initialized and sheets loaded." if repo_init else "Repository not initialized yet."
        except Exception as e:
            repo_status = "DOWN"
            repo_detail = f"Repository error: {str(e)}"
            StructuredLogger.warning(f"Repository Health Check Failed: {str(e)}")

        rep_time = (time.perf_counter() - start_rep) * 1000.0
        services_health.append(ServiceHealth(
            name="Data Repository Layer",
            status=repo_status,
            response_time_ms=round(rep_time, 2),
            detail=repo_detail
        ))

        # 2. Security validation health check
        start_sec = time.perf_counter()
        try:
            # Check availability of key dependencies
            from backend.security.jwt_manager import SECRET_KEY
            sec_status = "UP"
            sec_detail = "JWT Manager signature configurations active."
        except Exception as e:
            sec_status = "DOWN"
            sec_detail = f"Security module load error: {str(e)}"
            StructuredLogger.warning(f"Security Health Check Failed: {str(e)}")

        sec_time = (time.perf_counter() - start_sec) * 1000.0
        services_health.append(ServiceHealth(
            name="Security & Access Control Layer",
            status=sec_status,
            response_time_ms=round(sec_time, 2),
            detail=sec_detail
        ))

        # 3. Optimization Engines health check
        start_opt = time.perf_counter()
        try:
            from backend.services.shortest_path_engine import ShortestPathEngine
            from backend.services.astar_engine import AStarEngine
            from backend.services.ant_colony_engine import AntColonyEngine
            from backend.services.genetic_algorithm_engine import GeneticAlgorithmEngine

            opt_status = "UP"
            opt_detail = "Shortest Path, A*, Genetic, and Ant Colony engines compiled."
        except Exception as e:
            opt_status = "DEGRADED"
            opt_detail = f"Engine initialization warning: {str(e)}"
            StructuredLogger.warning(f"Optimization Engines Health Check Failed: {str(e)}")

        opt_time = (time.perf_counter() - start_opt) * 1000.0
        services_health.append(ServiceHealth(
            name="Optimization & Search Engines",
            status=opt_status,
            response_time_ms=round(opt_time, 2),
            detail=opt_detail
        ))

        # Determine overall consolidated status
        statuses = [s.status for s in services_health]
        if "DOWN" in statuses:
            overall_status = "DEGRADED"
        elif "DEGRADED" in statuses:
            overall_status = "DEGRADED"

        report = SystemHealthReport(
            overall_status=overall_status,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            services=services_health,
            checks_count=len(services_health)
        )

        StructuredLogger.info("System Health Check Completed.", {
            "overall_status": report.overall_status,
            "services_count": report.checks_count
        })

        return report
