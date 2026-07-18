import pandas as pd
from typing import Dict, Tuple
import time

from backend.services.pipeline import DataProcessingPipeline
from backend.models.processed_dataset import PipelineReport, ProcessingSummary
from backend.utils.logger import logger

class DataProcessorService:
    """Orchestrator service executing the processing pipeline across all dataset sheets."""

    def __init__(self):
        self.pipeline = DataProcessingPipeline()

    def process_dataset(self, raw_sheets: Dict[str, pd.DataFrame]) -> Tuple[Dict[str, pd.DataFrame], PipelineReport]:
        """Runs the processing pipeline across all sheets.
        
        Args:
            raw_sheets: Dictionary of raw loaded DataFrames.
            
        Returns:
            Tuple[Dict[str, pd.DataFrame], PipelineReport]: Processed DataFrames and global report.
        """
        logger.info("Pipeline Started: processing dataset.")
        start_time = time.perf_counter()
        
        report = PipelineReport()
        processed_sheets: Dict[str, pd.DataFrame] = {}
        
        total_rows_processed = 0
        total_cols_processed = 0
        total_missing_handled = 0
        total_duplicates_removed = 0
        total_columns_converted = []
        total_quality_score = 0.0
        success_count = 0

        for sheet_name, df in raw_sheets.items():
            try:
                processed_df, summary = self.pipeline.run_sheet(df, sheet_name)
                processed_sheets[sheet_name] = processed_df
                report.sheet_summaries[sheet_name] = summary
                
                # Accumulate stats
                total_rows_processed += summary.rows_processed
                total_cols_processed += summary.cols_processed
                total_missing_handled += summary.missing_values_handled
                total_duplicates_removed += summary.duplicates_removed
                total_columns_converted.extend([f"{sheet_name}.{c}" for c in summary.columns_converted])
                total_quality_score += summary.quality_score
                
                if summary.status == "SUCCESS":
                    success_count += 1
            except Exception as e:
                logger.error(f"Failed processing sheet '{sheet_name}' in orchestrator: {str(e)}")
                processed_sheets[sheet_name] = df
                
        # Calculate global summary statistics
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        sheet_count = len(raw_sheets)
        
        global_summary = ProcessingSummary(
            rows_processed=total_rows_processed,
            cols_processed=total_cols_processed,
            missing_values_handled=total_missing_handled,
            duplicates_removed=total_duplicates_removed,
            columns_converted=total_columns_converted,
            duration_ms=duration_ms,
            quality_score=round(total_quality_score / sheet_count, 2) if sheet_count > 0 else 100.0,
            status="SUCCESS" if success_count == sheet_count else "WARNING"
        )
        
        if sheet_count == 0:
            global_summary.status = "FAILED"
            
        report.summary = global_summary
        
        logger.info(f"Pipeline Finished: Processed {sheet_count} sheets in {duration_ms} ms. Status: {global_summary.status}, Quality Score: {global_summary.quality_score}")
        
        return processed_sheets, report
