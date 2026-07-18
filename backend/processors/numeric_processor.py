import pandas as pd
from typing import Tuple, List

from backend.config import COLUMN_TYPES
from backend.utils.logger import logger

class NumericProcessor:
    """Processor to coerce numeric fields and handle null/missing values gracefully."""

    @staticmethod
    def process(df: pd.DataFrame, sheet_name: str) -> Tuple[pd.DataFrame, int, List[str]]:
        """Ensures numeric columns have correct float/int types, filling nulls with default/median values.
        
        Args:
            df: DataFrame to process.
            sheet_name: Name of the sheet being processed.
            
        Returns:
            Tuple[pd.DataFrame, int, List[str]]: Processed DataFrame, count of nulls handled, list of converted columns.
        """
        processed_df = df.copy()
        nulls_handled = 0
        converted_cols = []
        
        sheet_types = COLUMN_TYPES.get(sheet_name, {})
        
        for col, col_type in sheet_types.items():
            if col in processed_df.columns and col_type == "numeric":
                # Check if it is not already numeric
                if not pd.api.types.is_numeric_dtype(processed_df[col]):
                    try:
                        # Coerce invalid values to NaN
                        processed_df[col] = pd.to_numeric(processed_df[col], errors='coerce')
                        converted_cols.append(col)
                        logger.info(f"NumericProcessor: Coerced column '{col}' in '{sheet_name}' to numeric.")
                    except Exception as e:
                        logger.error(f"NumericProcessor Error: Failed coercing '{col}' in '{sheet_name}': {str(e)}")
                        continue

                # Handle null values in numeric column without deleting records
                null_mask = processed_df[col].isnull()
                null_count = int(null_mask.sum())
                
                if null_count > 0:
                    # Determine fill value: median if it has valid values, else default to 0 or 0.0
                    valid_values = processed_df[col].dropna()
                    if len(valid_values) > 0:
                        fill_value = valid_values.median()
                    else:
                        fill_value = 0.0
                        
                    # Specific column defaults
                    if col == "Quantity":
                        fill_value = int(fill_value) if fill_value > 0 else 1
                        
                    processed_df.loc[null_mask, col] = fill_value
                    nulls_handled += null_count
                    logger.info(f"NumericProcessor: Filled {null_count} nulls in '{col}' of '{sheet_name}' with value '{fill_value}'.")
                    
        return processed_df, nulls_handled, converted_cols
