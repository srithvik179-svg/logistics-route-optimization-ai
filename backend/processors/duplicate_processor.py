import pandas as pd
from typing import Tuple
from backend.utils.logger import logger

class DuplicateProcessor:
    """Processor to detect and remove duplicate rows from DataFrames."""

    @staticmethod
    def process(df: pd.DataFrame, sheet_name: str) -> Tuple[pd.DataFrame, int]:
        """Removes duplicate rows from the DataFrame.
        
        Args:
            df: DataFrame to process.
            sheet_name: Name of the sheet being processed.
            
        Returns:
            Tuple[pd.DataFrame, int]: Processed DataFrame and number of duplicate rows removed.
        """
        initial_row_count = len(df)
        
        if initial_row_count == 0:
            return df, 0
            
        # Drop duplicates, keeping the first occurrence
        processed_df = df.drop_duplicates(keep="first")
        removed_count = initial_row_count - len(processed_df)
        
        if removed_count > 0:
            logger.info(f"DuplicateProcessor: Removed {removed_count} duplicate rows from '{sheet_name}'.")
            
        return processed_df, removed_count
