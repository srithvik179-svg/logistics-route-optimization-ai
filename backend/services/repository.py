import pandas as pd
from typing import Dict, List, Any, Optional
import os

from backend.config import DEFAULT_DATASET_PATH
from backend.services.dataset_loader import DatasetLoader
from backend.validators.dataset_validator import DatasetValidator
from backend.services.state_manager import state_manager
from backend.utils.logger import logger
from backend.models.repository_models import (
    TransactionRecord,
    HubRecord,
    TPRRecord,
    PartRecord,
    SummaryRecord
)

class DataRepository:
    """Centralized Data Repository Layer isolating raw Excel data from business logic."""

    def __init__(self, loader: Optional[DatasetLoader] = None):
        self._loader = loader or DatasetLoader(DEFAULT_DATASET_PATH)
        self._sheets: Dict[str, pd.DataFrame] = {}
        self._is_loaded = False
        logger.info("DataRepository instance created.")

    def initialize(self) -> None:
        """Loads and validates the dataset, initializing in-memory cache and state manager."""
        logger.info("Initializing DataRepository...")
        try:
            # 1. Fetch metadata and load data frames
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
                
            # 4. Update Application State Manager
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
        return len(self._sheets[sheet])

    def get_column_count(self, sheet: str) -> int:
        """Returns the column count of a sheet, or 0 if it doesn't exist."""
        if not self.sheet_exists(sheet):
            logger.warning(f"Repository Warning: Attempted to get column count of missing sheet '{sheet}'")
            return 0
        return len(self._sheets[sheet].columns)

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

    # Domain specific queries returning structured Pydantic models
    def get_all_transactions(self) -> List[TransactionRecord]:
        """Exposes typed Logistics Transactions records."""
        logger.info("Repository Access: get_all_transactions")
        records = self.get_sheet("Logistics_Transactions")
        typed_records = []
        for r in records:
            try:
                # Handle possible date-time conversions to string format
                for date_col in ["Order_Date", "Delivery_Date"]:
                    if r.get(date_col) is not None:
                        # Convert Timestamp objects or strings to ISO strings
                        if hasattr(r[date_col], "isoformat"):
                            r[date_col] = r[date_col].isoformat()
                        else:
                            r[date_col] = str(r[date_col])
                typed_records.append(TransactionRecord(**r))
            except Exception as e:
                logger.error(f"Repository Error: Failed parsing TransactionRecord: {str(e)} | Row: {r}")
        return typed_records

    def get_hubs(self) -> List[HubRecord]:
        """Exposes typed Hub Location Master records."""
        logger.info("Repository Access: get_hubs")
        records = self.get_sheet("Hub_Location_Master")
        typed_records = []
        for r in records:
            try:
                typed_records.append(HubRecord(**r))
            except Exception as e:
                logger.error(f"Repository Error: Failed parsing HubRecord: {str(e)} | Row: {r}")
        return typed_records

    def get_repair_centers(self) -> List[TPRRecord]:
        """Exposes typed Repair Center Master (TPR) records."""
        logger.info("Repository Access: get_repair_centers")
        # Try both 'TPR_Master' or synonym 'Repair_Center_Master'
        sheet_name = "TPR_Master" if self.sheet_exists("TPR_Master") else "Repair_Center_Master"
        records = self.get_sheet(sheet_name)
        typed_records = []
        for r in records:
            try:
                # Map synonym keys if necessary (e.g. Repair_Center_ID -> TPR_ID)
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
        """Exposes typed Parts Master records."""
        logger.info("Repository Access: get_parts")
        records = self.get_sheet("Parts_Master")
        typed_records = []
        for r in records:
            try:
                typed_records.append(PartRecord(**r))
            except Exception as e:
                logger.error(f"Repository Error: Failed parsing PartRecord: {str(e)} | Row: {r}")
        return typed_records

    def get_summary(self) -> List[SummaryRecord]:
        """Exposes typed Summary Dashboard records."""
        logger.info("Repository Access: get_summary")
        records = self.get_sheet("Summary_Dashboard")
        typed_records = []
        for r in records:
            try:
                typed_records.append(SummaryRecord(**r))
            except Exception as e:
                logger.error(f"Repository Error: Failed parsing SummaryRecord: {str(e)} | Row: {r}")
        return typed_records

# Global repository instance
repository = DataRepository()
