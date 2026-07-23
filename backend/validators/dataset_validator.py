import pandas as pd
from typing import Dict, List, Any

from backend.config import REQUIRED_SHEETS, EXPECTED_COLUMNS, COLUMN_TYPES
from backend.models.dataset_model import (
    DatasetMetadata,
    DatasetValidationReport,
    SheetValidationReport,
    ColumnValidationDetail
)
from backend.utils.logger import logger

class DatasetValidator:
    """Service to validate the integrity, schema, and quality of the dataset."""

    @staticmethod
    def validate(metadata: DatasetMetadata, sheets_data: Dict[str, pd.DataFrame]) -> DatasetValidationReport:
        """Validates the structure, columns, types, and quality of the loaded workbook sheets.
        
        Args:
            metadata: DatasetMetadata object.
            sheets_data: Dict mapping sheet names to Pandas DataFrames.
            
        Returns:
            DatasetValidationReport containing results for all checks.
        """
        logger.info("Starting dataset validation...")
        report = DatasetValidationReport()
        
        if not metadata.exists:
            report.is_valid = False
            report.global_errors.append("Dataset file does not exist.")
            logger.error("Validation failed: Dataset file does not exist.")
            return report

        if metadata.is_corrupt:
            report.is_valid = False
            report.global_errors.append("Dataset file is corrupted or unreadable.")
            logger.error("Validation failed: Dataset file is corrupted.")
            return report

        if metadata.is_empty:
            report.is_valid = False
            report.global_errors.append("Dataset file is empty.")
            logger.error("Validation failed: Dataset file is empty.")
            return report

        # Check required sheets
        for required_sheet in REQUIRED_SHEETS:
            sheet_report = SheetValidationReport(sheet_name=required_sheet)
            
            if required_sheet == "Summary_Dashboard":
                sheet_report.exists = required_sheet in sheets_data
                sheet_report.is_valid = True
                report.sheets[required_sheet] = sheet_report
                continue

            if required_sheet not in sheets_data:
                sheet_report.exists = False
                sheet_report.is_valid = False
                sheet_report.errors.append(f"Sheet '{required_sheet}' is missing.")
                report.sheets[required_sheet] = sheet_report
                report.is_valid = False
                logger.error(f"Validation Error: Sheet '{required_sheet}' is missing.")
                continue
                
            sheet_report.exists = True
            df = sheets_data[required_sheet]
            sheet_report.row_count = len(df)
            sheet_report.col_count = len(df.columns)
            
            # 1. Missing columns
            expected_cols = EXPECTED_COLUMNS.get(required_sheet, [])
            missing_cols = [col for col in expected_cols if col not in df.columns]
            if missing_cols:
                sheet_report.missing_columns = missing_cols
                sheet_report.is_valid = False
                sheet_report.errors.append(f"Missing columns: {', '.join(missing_cols)}")
                logger.error(f"Validation Error: Sheet '{required_sheet}' is missing columns: {missing_cols}")

            # 2. Empty rows (entire row is NaN)
            empty_row_count = int(df.isnull().all(axis=1).sum())
            sheet_report.empty_rows = empty_row_count
            if empty_row_count > 0:
                sheet_report.warnings.append(f"Found {empty_row_count} completely empty rows.")
                logger.warning(f"Validation Warning: Sheet '{required_sheet}' has {empty_row_count} empty rows.")

            # 3. Duplicate rows (excluding empty rows)
            # We filter out completely empty rows first to count actual data duplicates
            non_empty_df = df[~df.isnull().all(axis=1)]
            duplicate_count = int(non_empty_df.duplicated().sum())
            sheet_report.duplicate_rows = duplicate_count
            if duplicate_count > 0:
                sheet_report.warnings.append(f"Found {duplicate_count} duplicate data rows.")
                logger.warning(f"Validation Warning: Sheet '{required_sheet}' has {duplicate_count} duplicate rows.")

            # 4. Column-level validation (Data Types & Missing Values)
            col_types = COLUMN_TYPES.get(required_sheet, {})
            for col in expected_cols:
                if col in df.columns:
                    # Missing values count
                    missing_val_count = int(df[col].isnull().sum())
                    if missing_val_count > 0:
                        sheet_report.warnings.append(f"Column '{col}' has {missing_val_count} missing values.")
                        logger.warning(f"Validation Warning: Sheet '{required_sheet}', Column '{col}' has {missing_val_count} missing values.")

                    # Type checking
                    expected_type = col_types.get(col, "object")
                    actual_type = str(df[col].dtype)
                    is_type_valid = True
                    
                    if expected_type == "numeric":
                        # Check if column can be coerced to numeric or is numeric
                        if not pd.api.types.is_numeric_dtype(df[col]):
                            # Try converting
                            try:
                                pd.to_numeric(df[col].dropna())
                                # Coercible, but warning that it was loaded as object/string
                                sheet_report.warnings.append(f"Column '{col}' has non-numeric type '{actual_type}' but can be parsed as numeric.")
                            except Exception:
                                is_type_valid = False
                                sheet_report.errors.append(f"Column '{col}' has invalid data type. Expected numeric, got '{actual_type}'.")
                                logger.error(f"Validation Error: Sheet '{required_sheet}', Column '{col}' type mismatch. Expected numeric, got '{actual_type}'.")
                    
                    elif expected_type == "datetime":
                        if pd.api.types.is_datetime64_any_dtype(df[col]):
                            # Column is already proper datetime — nothing to report
                            pass
                        else:
                            # Column is still object/string — try parsing
                            non_null = df[col].dropna()
                            if len(non_null) == 0:
                                # All null — treated as valid, nothing to validate
                                pass
                            else:
                                converted = pd.to_datetime(non_null, errors="coerce")
                                failure_rate = converted.isna().sum() / len(non_null)

                                if failure_rate > 0.10:
                                    # More than 10 % of values cannot be parsed — real error
                                    is_type_valid = False
                                    sheet_report.errors.append(
                                        f"Column '{col}' has invalid data type. Expected datetime, got '{actual_type}' "
                                        f"({failure_rate*100:.1f}% of values are not parseable as dates)."
                                    )
                                    logger.error(
                                        f"Validation Error: Sheet '{required_sheet}', Column '{col}' — "
                                        f"{failure_rate*100:.1f}% of values are unparseable dates."
                                    )
                                # else: all or almost all values parse fine — silently accept it

                    # Record details — read dtype fresh so it reflects the already-coerced column
                    runtime_type = str(df[col].dtype)
                    sheet_report.invalid_columns.append(ColumnValidationDetail(
                        name=col,
                        expected_type=expected_type,
                        actual_type=runtime_type,
                        is_valid=is_type_valid,
                        missing_count=missing_val_count
                    ))
                    
                    if not is_type_valid:
                        sheet_report.is_valid = False

            # Set global validity if any sheet is invalid
            if not sheet_report.is_valid:
                report.is_valid = False
                
            report.sheets[required_sheet] = sheet_report

        logger.info(f"Dataset validation completed. Overall Validity: {report.is_valid}")
        return report
