import os
import pandas as pd
from datetime import datetime
from typing import Dict, Tuple, Any

from backend.config import DEFAULT_DATASET_PATH, COLUMN_TYPES
from backend.models.dataset_model import DatasetMetadata, DatasetModel
from backend.utils.logger import logger

class DatasetLoader:
    """Service to safely detect, verify, and load Excel workbooks."""

    def __init__(self, file_path: str = DEFAULT_DATASET_PATH):
        self.file_path = file_path

    def get_metadata(self) -> DatasetMetadata:
        """Inspects the dataset file and returns metadata without loading full data."""
        metadata = DatasetMetadata(file_path=self.file_path)
        
        if not os.path.exists(self.file_path):
            logger.warning(f"Dataset file not found at path: {self.file_path}")
            metadata.exists = False
            return metadata

        metadata.exists = True
        
        # Get file stats
        try:
            stats = os.stat(self.file_path)
            metadata.file_size_bytes = stats.st_size
            metadata.last_modified = datetime.fromtimestamp(stats.st_mtime).isoformat()
            
            if metadata.file_size_bytes == 0:
                logger.error(f"Dataset file is empty (0 bytes): {self.file_path}")
                metadata.is_empty = True
                return metadata
                
        except Exception as e:
            logger.error(f"Error accessing file statistics for {self.file_path}: {str(e)}")
            metadata.is_corrupt = True
            return metadata

        # Verify Excel integrity and get sheet names
        try:
            with pd.ExcelFile(self.file_path, engine="openpyxl") as xls:
                metadata.sheet_names = xls.sheet_names
            logger.info(f"Dataset detected and verified. Sheets found: {metadata.sheet_names}")
        except Exception as e:
            logger.error(f"Failed to open Excel workbook (file may be corrupted): {str(e)}")
            metadata.is_corrupt = True
            
        return metadata

    def load(self) -> Tuple[DatasetMetadata, Dict[str, pd.DataFrame]]:
        """Loads all sheets from the Excel file if verified.
        
        Returns:
            Tuple[DatasetMetadata, Dict[str, pd.DataFrame]]: Metadata and loaded sheets.
        """
        metadata = self.get_metadata()
        sheets_data: Dict[str, pd.DataFrame] = {}

        if not metadata.exists or metadata.is_empty or metadata.is_corrupt:
            logger.error("Skipping sheet loading due to dataset state errors.")
            return metadata, sheets_data

        logger.info(f"Opening workbook: {self.file_path}")
        try:
            with pd.ExcelFile(self.file_path, engine="openpyxl") as xls:
                for sheet in xls.sheet_names:
                    try:
                        # Load sheet raw
                        df = pd.read_excel(xls, sheet_name=sheet)

                        # Auto-parse datetime columns immediately at load time
                        # so validation sees datetime64 dtype, never 'object'
                        df = DatasetLoader._coerce_date_columns(df, sheet)

                        sheets_data[sheet] = df
                        logger.info(f"Successfully loaded sheet '{sheet}' with {len(df)} rows and {len(df.columns)} columns.")
                    except Exception as sheet_err:
                        logger.error(f"Error loading sheet '{sheet}': {str(sheet_err)}")
                        # Continue loading other sheets
        except Exception as e:
            logger.critical(f"Critical error reading workbook sheets: {str(e)}")
            metadata.is_corrupt = True

        return metadata, sheets_data

    @staticmethod
    def _coerce_date_columns(df: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
        """Converts all recognized date columns to datetime64 at load time.

        A column is treated as a date column if:
        - Its name is declared as "datetime" in COLUMN_TYPES config, OR
        - Its name contains the substrings 'date' or 'time' (case-insensitive)
          and the majority of non-null values are parseable as dates.

        Conversion uses errors="coerce" so unparseable values become NaT
        instead of raising exceptions.  The original object column is only
        kept intact if fewer than 50 % of non-null values can be parsed.
        """
        sheet_types = COLUMN_TYPES.get(sheet_name, {})
        df = df.copy()

        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                # Already datetime — nothing to do
                continue

            is_declared_datetime = sheet_types.get(col) == "datetime"
            is_date_named = "date" in col.lower() or "time" in col.lower()

            if not (is_declared_datetime or is_date_named):
                continue

            # Attempt conversion
            converted = pd.to_datetime(df[col], errors="coerce")
            non_null_original = df[col].notna().sum()

            if non_null_original == 0:
                # All values are null — accept the conversion (all NaT is fine)
                df[col] = converted
                continue

            success_rate = converted.notna().sum() / non_null_original

            if success_rate >= 0.5:
                # Majority parsed successfully — apply the conversion
                df[col] = converted
                logger.debug(
                    f"DatasetLoader: Auto-converted '{col}' in '{sheet_name}' to datetime "
                    f"({success_rate*100:.1f}% of values parsed successfully)."
                )
            else:
                # Parsing largely failed — leave the column untouched
                logger.warning(
                    f"DatasetLoader: Skipped auto-conversion of '{col}' in '{sheet_name}' "
                    f"— only {success_rate*100:.1f}% of values are valid dates."
                )

        return df
