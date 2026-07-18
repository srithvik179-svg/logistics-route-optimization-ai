import pandas as pd
from typing import Dict, Tuple, List, Any
import time

from backend.processors.text_processor import TextProcessor
from backend.processors.numeric_processor import NumericProcessor
from backend.processors.date_processor import DateProcessor
from backend.processors.duplicate_processor import DuplicateProcessor
from backend.processors.quality_processor import QualityProcessor
from backend.models.processed_dataset import ProcessingSummary
from backend.utils.logger import logger

class DataProcessingPipeline:
    """Sequentially executes text, numeric, date, and duplicate transformations on DataFrames."""

    def __init__(self):
        logger.info("DataProcessingPipeline instantiated.")

    def run_sheet(self, df: pd.DataFrame, sheet_name: str) -> Tuple[pd.DataFrame, ProcessingSummary]:
        """Runs the complete cleaning pipeline on a single sheet.
        
        Args:
            df: Raw input DataFrame.
            sheet_name: Name of the sheet.
            
        Returns:
            Tuple[pd.DataFrame, ProcessingSummary]: Cleaned DataFrame and processing stats.
        """
        start_time = time.perf_counter()
        summary = ProcessingSummary()
        summary.rows_processed = len(df)
        summary.cols_processed = len(df.columns)
        
        # 1. Assess initial Quality Score
        summary.quality_score = QualityProcessor.calculate_score(df, sheet_name)
        
        if len(df) == 0:
            summary.status = "SUCCESS"
            summary.duration_ms = (time.perf_counter() - start_time) * 1000
            return df, summary

        logger.info(f"Running processing pipeline on sheet '{sheet_name}' (rows={len(df)}, quality={summary.quality_score})")

        try:
            # Stage A: Remove Duplicates
            df_dedup, dups_removed = DuplicateProcessor.process(df, sheet_name)
            summary.duplicates_removed = dups_removed
            
            # Stage B: Clean and Standardize Text
            df_text, text_mods = TextProcessor.process(df_dedup, sheet_name)
            
            # Stage C: Clean and Coerce Numeric Fields
            df_num, nulls_filled, num_conversions = NumericProcessor.process(df_text, sheet_name)
            summary.missing_values_handled += nulls_filled
            summary.columns_converted.extend(num_conversions)
            
            # Stage D: Standardize and Enrich Dates
            df_date, date_conversions = DateProcessor.process(df_num, sheet_name)
            summary.columns_converted.extend(date_conversions)
            
            # Final output sheet
            final_df = df_date
            
            # Calculate final row & col specs
            summary.rows_processed = len(final_df)
            summary.cols_processed = len(final_df.columns)
            summary.status = "SUCCESS"
            
        except Exception as e:
            logger.error(f"Pipeline Stage Failure in sheet '{sheet_name}': {str(e)}")
            summary.status = "FAILED"
            final_df = df
            
        summary.duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(f"Finished processing sheet '{sheet_name}' in {summary.duration_ms} ms. Status: {summary.status}")
        
        return final_df, summary
