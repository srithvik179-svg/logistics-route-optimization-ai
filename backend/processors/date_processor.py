import pandas as pd
from typing import Tuple, List
from backend.config import COLUMN_TYPES
from backend.utils.logger import logger

class DateProcessor:
    """Processor to detect date columns, convert them to datetimes, and derive calendar attributes."""

    @staticmethod
    def process(df: pd.DataFrame, sheet_name: str) -> Tuple[pd.DataFrame, List[str]]:
        """Automatically detects date columns, normalizes them, and generates derived calendar fields.
        
        Args:
            df: DataFrame to process.
            sheet_name: Name of the sheet being processed.
            
        Returns:
            Tuple[pd.DataFrame, List[str]]: Processed DataFrame and list of converted date columns.
        """
        processed_df = df.copy()
        converted_cols = []
        
        # 1. Identify date columns
        sheet_types = COLUMN_TYPES.get(sheet_name, {})
        date_cols = []
        
        for col in processed_df.columns:
            # Check configuration or name heuristics
            is_date_configured = sheet_types.get(col) == "datetime"
            is_date_named = "date" in col.lower() or "time" in col.lower()
            
            if is_date_configured or is_date_named:
                date_cols.append(col)
                
        # 2. Parse and normalize each date column
        for col in date_cols:
            try:
                # Coerce to datetime
                processed_df[col] = pd.to_datetime(processed_df[col], errors='coerce')
                converted_cols.append(col)
                
                # Check if we have any valid dates before deriving attributes
                if processed_df[col].notnull().any():
                    # Handle NaNs in date columns: fill missing dates with order date or default current time
                    # To avoid mutating future values incorrectly, we preserve NaNs where appropriate,
                    # but fill missing values with the median date of the column so calculations don't fail.
                    valid_dates = processed_df[col].dropna()
                    median_date = valid_dates.iloc[len(valid_dates)//2] if len(valid_dates) > 0 else pd.Timestamp.now()
                    
                    processed_df[col] = processed_df[col].fillna(median_date)
                    
                    # Generate derived columns with prefixed names (e.g. Order_Date_Year)
                    processed_df[f"{col}_Year"] = processed_df[col].dt.year.astype(int)
                    processed_df[f"{col}_Month"] = processed_df[col].dt.month.astype(int)
                    processed_df[f"{col}_Quarter"] = processed_df[col].dt.quarter.astype(int)
                    processed_df[f"{col}_Week"] = processed_df[col].dt.isocalendar().week.astype(int)
                    processed_df[f"{col}_Day"] = processed_df[col].dt.day.astype(int)
                    processed_df[f"{col}_Day_Name"] = processed_df[col].dt.day_name()
                    
                    logger.info(f"DateProcessor: Successfully processed and enriched date column '{col}' in '{sheet_name}'.")
            except Exception as e:
                logger.error(f"DateProcessor Error: Failed processing date column '{col}' in '{sheet_name}': {str(e)}")
                
        return processed_df, converted_cols
