import pandas as pd
from typing import Dict, Any

from backend.config import EXPECTED_COLUMNS, COLUMN_TYPES

class QualityProcessor:
    """Processor to calculate Data Quality Scores for sheets and datasets."""

    @staticmethod
    def calculate_score(df: pd.DataFrame, sheet_name: str) -> float:
        """Calculates a data quality score (0 to 100) based on nulls, duplicates, and type mismatches.
        
        Args:
            df: Raw input DataFrame before pipeline transformations.
            sheet_name: Name of the sheet.
            
        Returns:
            float: Quality score out of 100.
        """
        rows = len(df)
        cols = len(df.columns)
        
        if rows == 0 or cols == 0:
            return 100.0
            
        total_cells = rows * cols
        
        # 1. Null cell counts
        null_cells = int(df.isnull().sum().sum())
        
        # 2. Duplicate rows impact
        duplicate_rows = int(df.duplicated().sum())
        duplicate_cells = duplicate_rows * cols
        
        # 3. Datatype mismatch checks
        mismatched_cells = 0
        expected_cols = EXPECTED_COLUMNS.get(sheet_name, [])
        col_types = COLUMN_TYPES.get(sheet_name, {})
        
        for col in expected_cols:
            if col in df.columns:
                expected_type = col_types.get(col, "object")
                
                if expected_type == "numeric":
                    # Check how many values are not numeric (and not null)
                    non_nulls = df[col].dropna()
                    for val in non_nulls:
                        try:
                            float(str(val))
                        except ValueError:
                            mismatched_cells += 1
                            
                elif expected_type == "datetime":
                    non_nulls = df[col].dropna()
                    for val in non_nulls:
                        try:
                            pd.to_datetime(val)
                        except (ValueError, TypeError):
                            mismatched_cells += 1

        # Calculate score (deduct penalty from 100)
        total_penalties = null_cells + duplicate_cells + mismatched_cells
        penalty_ratio = total_penalties / total_cells
        score = 100.0 * (1.0 - penalty_ratio)
        
        # Clip score between 0.0 and 100.0
        return max(0.0, min(100.0, round(score, 2)))
