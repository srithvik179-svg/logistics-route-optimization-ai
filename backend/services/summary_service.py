import datetime
from typing import Dict, Any
from backend.services.state_manager import state_manager
from backend.services.repository import repository
from backend.utils.logger import logger

class SummaryService:
    """Service to generate system status summaries and executive platform details."""

    @staticmethod
    def generate_summary() -> Dict[str, Any]:
        """Gathers catalog refresh details and returns structured metadata details for dashboards."""
        logger.info("SummaryService: Generating executive summary metrics.")
        try:
            state = state_manager.get_state()
            
            # Count total rows across all processed cached sheets
            total_records = 0
            for sheet in repository._processed_sheets.values():
                total_records += len(sheet)
                
            return {
                "dataset_status": "LOADED" if state.dataset_loaded else "NOT_FOUND",
                "repository_status": state.repository_health,
                "processing_status": "SUCCESS" if state.validation_passed else "WARNING",
                "last_refresh_time": state.last_load_time if state.last_load_time else None,
                "total_processed_records": total_records
            }
        except Exception as e:
            logger.error(f"SummaryService Error: Failed generating summary info: {str(e)}")
            return {
                "dataset_status": "OFFLINE",
                "repository_status": "DEGRADED",
                "processing_status": "FAILED",
                "last_refresh_time": None,
                "total_processed_records": 0
            }
