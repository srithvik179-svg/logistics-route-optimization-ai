"""Metrics collector tracking runtime statistics, cache hit rates, active threads, and tracebacks."""

import time
import threading
from typing import List, Dict, Any
from backend.models.trace_event import TraceEvent


class MetricsCollector:
    """Thread-safe collector for api statistics, cache performance, and engine runs."""

    _lock = threading.Lock()
    
    # Cumulative API metrics
    _total_requests = 0
    _failed_requests = 0
    _total_response_time_ms = 0.0
    _active_requests = 0
    
    # Path request counter
    _api_path_counts: Dict[str, int] = {}
    _api_error_counts: Dict[int, int] = {}

    # Cache hit/miss metrics
    _cache_hits = 0
    _cache_misses = 0

    # Engine traces and exceptions logs
    _recent_engine_traces: List[TraceEvent] = []
    _recent_exceptions: List[str] = []
    _max_buffer_size = 50

    @classmethod
    def record_request_start(cls) -> None:
        """Increments active requests count."""
        with cls._lock:
            cls._active_requests += 1

    @classmethod
    def record_request_end(cls, path: str, elapsed_ms: float, status_code: int) -> None:
        """Updates request totals, latencies, path counts, and status errors.

        Args:
            path: Target URL path.
            elapsed_ms: Elapsed execution milliseconds.
            status_code: Returned HTTP status code.
        """
        with cls._lock:
            if cls._active_requests > 0:
                cls._active_requests -= 1
            cls._total_requests += 1
            cls._total_response_time_ms += elapsed_ms
            cls._api_path_counts[path] = cls._api_path_counts.get(path, 0) + 1

            if status_code >= 400:
                cls._failed_requests += 1
                cls._api_error_counts[status_code] = cls._api_error_counts.get(status_code, 0) + 1

    @classmethod
    def record_cache_hit(cls) -> None:
        """Increments cache hit metrics."""
        with cls._lock:
            cls._cache_hits += 1

    @classmethod
    def record_cache_miss(cls) -> None:
        """Increments cache miss metrics."""
        with cls._lock:
            cls._cache_misses += 1

    @classmethod
    def record_engine_run(cls, engine_name: str, elapsed_ms: float, success: bool, error_msg: str = None) -> None:
        """Records an optimization engine run trace.

        Args:
            engine_name: Name of the engine.
            elapsed_ms: Duration in milliseconds.
            success: Execution status success boolean.
            error_msg: Optional error string message.
        """
        import uuid
        trace = TraceEvent(
            trace_id=str(uuid.uuid4()),
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            service_name=engine_name,
            execution_time_ms=elapsed_ms,
            status="SUCCESS" if success else "ERROR",
            error_message=error_msg
        )
        with cls._lock:
            cls._recent_engine_traces.append(trace)
            if len(cls._recent_engine_traces) > cls._max_buffer_size:
                cls._recent_engine_traces.pop(0)

    @classmethod
    def record_exception(cls, message: str) -> None:
        """Records a traceback exception string."""
        with cls._lock:
            cls._recent_exceptions.append(message)
            if len(cls._recent_exceptions) > cls._max_buffer_size:
                cls._recent_exceptions.pop(0)

    @classmethod
    def get_snapshot_data(cls) -> Dict[str, Any]:
        """Gathers cumulative values into a raw stats dictionary."""
        with cls._lock:
            total_reqs = cls._total_requests
            failed_reqs = cls._failed_requests
            total_time = cls._total_response_time_ms
            hits = cls._cache_hits
            misses = cls._cache_misses
            traces = list(cls._recent_engine_traces)
            exceptions = list(cls._recent_exceptions)
            active = cls._active_requests

            path_counts = dict(cls._api_path_counts)
            error_counts = dict(cls._api_error_counts)

        avg_api_time = (total_time / total_reqs) if total_reqs > 0 else 0.0
        
        total_cache = hits + misses
        hit_ratio = (hits / total_cache) if total_cache > 0 else 1.0
        miss_ratio = (misses / total_cache) if total_cache > 0 else 0.0

        avg_engine_time = 0.0
        if traces:
            avg_engine_time = sum(t.execution_time_ms for t in traces) / len(traces)

        error_rate = (failed_reqs / total_reqs) if total_reqs > 0 else 0.0

        return {
            "api_response_time_avg": round(avg_api_time, 2),
            "engine_execution_time_avg": round(avg_engine_time, 2),
            "cache_hit_ratio": round(hit_ratio, 4),
            "cache_miss_ratio": round(miss_ratio, 4),
            "total_requests": total_reqs,
            "failed_requests": failed_reqs,
            "active_requests": active,
            "error_rate": round(error_rate, 4),
            "path_counts": path_counts,
            "error_counts": error_counts,
            "traces": traces,
            "exceptions": exceptions
        }
