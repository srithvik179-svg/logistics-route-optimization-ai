from pydantic import BaseModel, Field
from typing import List, Dict

class ProcessingSummary(BaseModel):
    rows_processed: int = 0
    cols_processed: int = 0
    missing_values_handled: int = 0
    duplicates_removed: int = 0
    columns_converted: List[str] = Field(default_factory=list)
    duration_ms: float = 0.0
    quality_score: float = 0.0
    status: str = "SUCCESS"  # "SUCCESS" | "WARNING" | "FAILED"

class PipelineReport(BaseModel):
    summary: ProcessingSummary = Field(default_factory=ProcessingSummary)
    sheet_summaries: Dict[str, ProcessingSummary] = Field(default_factory=dict)
