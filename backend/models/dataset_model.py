from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

class ColumnValidationDetail(BaseModel):
    name: str
    expected_type: str
    actual_type: str
    is_valid: bool
    missing_count: int = 0

class SheetValidationReport(BaseModel):
    sheet_name: str
    exists: bool = False
    row_count: int = 0
    col_count: int = 0
    duplicate_rows: int = 0
    empty_rows: int = 0
    missing_columns: List[str] = Field(default_factory=list)
    invalid_columns: List[ColumnValidationDetail] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    is_valid: bool = True

class DatasetValidationReport(BaseModel):
    is_valid: bool = True
    sheets: Dict[str, SheetValidationReport] = Field(default_factory=dict)
    global_errors: List[str] = Field(default_factory=list)
    global_warnings: List[str] = Field(default_factory=list)

class DatasetMetadata(BaseModel):
    file_path: str
    exists: bool = False
    file_size_bytes: int = 0
    last_modified: Optional[str] = None
    sheet_names: List[str] = Field(default_factory=list)
    is_corrupt: bool = False
    is_empty: bool = False

class DatasetModel:
    """Non-Pydantic container for holding raw pandas DataFrames and their metadata.
    Avoids slow Pydantic validation on large DataFrames.
    """
    def __init__(
        self,
        metadata: DatasetMetadata,
        sheets_data: Dict[str, Any],
        validation_report: Optional[DatasetValidationReport] = None
    ):
        self.metadata = metadata
        self.sheets_data = sheets_data  # Dictionary of sheet_name -> pd.DataFrame
        self.validation_report = validation_report
