import pandas as pd
from typing import Dict, List, Any, Optional
import os

from backend.config import DEFAULT_DATASET_PATH
from backend.services.dataset_loader import DatasetLoader
from backend.validators.dataset_validator import DatasetValidator
from backend.services.state_manager import state_manager
from backend.services.data_processor import DataProcessorService
from backend.models.processed_dataset import PipelineReport
from backend.utils.logger import logger
from backend.models.repository_models import (
    TransactionRecord,
    HubRecord,
    TPRRecord,
    PartRecord,
    SummaryRecord
)

class DataRepository:
    """Centralized Data Repository Layer isolating raw and processed Excel data from business logic."""

    def __init__(self, loader: Optional[DatasetLoader] = None):
        self._loader = loader or DatasetLoader(DEFAULT_DATASET_PATH)
        self._sheets: Dict[str, pd.DataFrame] = {}
        self._processed_sheets: Dict[str, pd.DataFrame] = {}
        self._pipeline_report: Optional[PipelineReport] = None
        self._is_loaded = False
        logger.info("DataRepository instance created.")

    def initialize(self) -> None:
        """Loads, validates, and processes the dataset, initializing in-memory caches and state manager."""
        logger.info("Initializing DataRepository...")
        try:
            # 1. Fetch metadata and load raw data frames
            metadata, sheets_data = self._loader.load()
            
            # 2. Run validator
            validation_report = DatasetValidator.validate(metadata, sheets_data)
            
            # 3. Store loaded sheets in-memory cache
            self._sheets = sheets_data
            self._is_loaded = metadata.exists and not metadata.is_corrupt and not metadata.is_empty
            
            # Determine health status based on validation
            health = "DEGRADED"
            if self._is_loaded:
                health = "HEALTHY" if validation_report.is_valid else "WARNING"
                
                # 4. Automatically run processing pipeline if loaded
                logger.info("Triggering data processing pipeline automatically...")
                processor = DataProcessorService()
                processed_sheets, pipeline_report = processor.process_dataset(self._sheets)
                self._processed_sheets = processed_sheets
                self._pipeline_report = pipeline_report
            else:
                self._processed_sheets = {}
                self._pipeline_report = None
                
            # 5. Update Application State Manager
            state_manager.update_state(
                dataset_loaded=self._is_loaded,
                validation_passed=validation_report.is_valid,
                repository_ready=self._is_loaded,
                repository_health=health
            )
            
            logger.info(f"Repository Initialized. State: Loaded={self._is_loaded}, Health={health}")
            
        except Exception as e:
            logger.error(f"Critical error during DataRepository initialization: {str(e)}")
            state_manager.update_state(
                dataset_loaded=False,
                validation_passed=False,
                repository_ready=False,
                repository_health="DEGRADED"
            )

    def is_initialized(self) -> bool:
        """Checks if the repository has been successfully initialized and contains cached data."""
        return self._is_loaded

    def list_available_sheets(self) -> List[str]:
        """Returns a list of all sheets loaded in-memory."""
        logger.info("Repository Access: list_available_sheets")
        return list(self._sheets.keys())

    def sheet_exists(self, name: str) -> bool:
        """Checks if a sheet exists in the repository cache."""
        exists = name in self._sheets
        logger.info(f"Repository Access: sheet_exists('{name}') -> {exists}")
        return exists

    def get_row_count(self, sheet: str) -> int:
        """Returns the row count of a sheet, or 0 if it doesn't exist."""
        if not self.sheet_exists(sheet):
            logger.warning(f"Repository Warning: Attempted to get row count of missing sheet '{sheet}'")
            return 0
        # Prefer row count of processed data if available
        df = self._processed_sheets.get(sheet) if self._processed_sheets else None
        if df is None:
            df = self._sheets[sheet]
        return len(df)

    def get_column_count(self, sheet: str) -> int:
        """Returns the column count of a sheet, or 0 if it doesn't exist."""
        if not self.sheet_exists(sheet):
            logger.warning(f"Repository Warning: Attempted to get column count of missing sheet '{sheet}'")
            return 0
        # Prefer column count of processed data if available
        df = self._processed_sheets.get(sheet) if self._processed_sheets else None
        if df is None:
            df = self._sheets[sheet]
        return len(df.columns)

    def get_sheet(self, name: str) -> List[Dict[str, Any]]:
        """Returns raw records from a sheet as list of dictionaries."""
        logger.info(f"Repository Access: get_sheet('{name}')")
        if not self.sheet_exists(name):
            logger.error(f"Repository Error: Sheet '{name}' not found.")
            return []
        
        # Replace NaN with None for JSON serialization compatibility
        df = self._sheets[name].copy()
        df = df.where(pd.notnull(df), None)
        return df.to_dict(orient="records")

    def get_processed_sheet(self, name: str) -> List[Dict[str, Any]]:
        """Returns processed/cleaned records from a sheet as list of dictionaries."""
        logger.info(f"Repository Access: get_processed_sheet('{name}')")
        if name not in self._processed_sheets:
            logger.error(f"Repository Error: Processed sheet '{name}' not found. Falling back to raw.")
            return self.get_sheet(name)
            
        df = self._processed_sheets[name].copy()
        # Convert Timestamp objects to string ISO format for JSON compatibility
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                # Fill NaNs first then convert
                df[col] = df[col].dt.strftime("%Y-%m-%d %H:%M:%S")
                
        # Replace NaN with None
        df = df.where(pd.notnull(df), None)
        return df.to_dict(orient="records")

    def get_pipeline_report(self) -> Optional[PipelineReport]:
        """Returns the report summary of the data processing pipeline."""
        return self._pipeline_report

    # Domain specific queries returning structured Pydantic models (from processed cache)
    def get_all_transactions(self) -> List[TransactionRecord]:
        """Exposes typed and cleaned Logistics Transactions records."""
        logger.info("Repository Access: get_all_transactions (processed)")
        records = self.get_processed_sheet("Logistics_Transactions")
        typed_records = []
        for r in records:
            try:
                # Basic Pydantic validation (ignores extra calendar columns generated dynamically)
                typed_records.append(TransactionRecord(**r))
            except Exception as e:
                logger.error(f"Repository Error: Failed parsing TransactionRecord: {str(e)} | Row: {r}")
        return typed_records

    def get_hubs(self) -> List[HubRecord]:
        """Exposes typed and cleaned Hub Location Master records."""
        logger.info("Repository Access: get_hubs (processed)")
        records = self.get_processed_sheet("Hub_Location_Master")
        typed_records = []
        for r in records:
            try:
                typed_records.append(HubRecord(**r))
            except Exception as e:
                logger.error(f"Repository Error: Failed parsing HubRecord: {str(e)} | Row: {r}")
        return typed_records

    def get_repair_centers(self) -> List[TPRRecord]:
        """Exposes typed and cleaned Repair Center Master (TPR) records."""
        logger.info("Repository Access: get_repair_centers (processed)")
        sheet_name = "TPR_Master" if self.sheet_exists("TPR_Master") else "Repair_Center_Master"
        records = self.get_processed_sheet(sheet_name)
        typed_records = []
        for r in records:
            try:
                mapped_record = {
                    "TPR_ID": r.get("TPR_ID") or r.get("Repair_Center_ID") or "",
                    "TPR_Name": r.get("TPR_Name") or r.get("Repair_Center_Name") or "",
                    "Coverage_Region": r.get("Coverage_Region") or "",
                    "SLA_Compliance_Target": r.get("SLA_Compliance_Target") or 0.0,
                    "Rating": r.get("Rating") or 0.0
                }
                typed_records.append(TPRRecord(**mapped_record))
            except Exception as e:
                logger.error(f"Repository Error: Failed parsing TPRRecord: {str(e)} | Row: {r}")
        return typed_records

    def get_parts(self) -> List[PartRecord]:
        """Exposes typed and cleaned Parts Master records."""
        logger.info("Repository Access: get_parts (processed)")
        records = self.get_processed_sheet("Parts_Master")
        typed_records = []
        for r in records:
            try:
                typed_records.append(PartRecord(**r))
            except Exception as e:
                logger.error(f"Repository Error: Failed parsing PartRecord: {str(e)} | Row: {r}")
        return typed_records

    def get_summary(self) -> List[SummaryRecord]:
        """Exposes typed Summary Dashboard records."""
        logger.info("Repository Access: get_summary (processed)")
        records = self.get_processed_sheet("Summary_Dashboard")
        typed_records = []
        for r in records:
            try:
                typed_records.append(SummaryRecord(**r))
            except Exception as e:
                logger.error(f"Repository Error: Failed parsing SummaryRecord: {str(e)} | Row: {r}")
        return typed_records

# Global repository instance
repository = DataRepository()
