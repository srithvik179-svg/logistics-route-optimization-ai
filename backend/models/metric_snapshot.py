"""Pydantic model representing a telemetry metric snapshot at a point in time."""

from pydantic import BaseModel, Field


class MetricSnapshot(BaseModel):
    """Holds core system metrics including throughput, error rates, latencies, and cache metrics."""
    timestamp: str = Field(description="ISO-8601 formatting snapshot timestamp")
    api_response_time_avg: float = Field(description="Average API response latency in milliseconds")
    engine_execution_time_avg: float = Field(description="Average optimization engine run latency in milliseconds")
    memory_usage_bytes: int = Field(description="Calculated process memory usage in bytes")
    cache_hit_ratio: float = Field(description="System-wide cache hits count ratio")
    cache_miss_ratio: float = Field(description="System-wide cache misses count ratio")
    request_throughput: float = Field(description="Incoming requests count per minute frequency")
    active_requests: int = Field(description="Count of currently active requests processing")
    failed_requests: int = Field(description="Total count of failed requests returned")
    error_rate: float = Field(description="Ratio of failed requests to total request count")
