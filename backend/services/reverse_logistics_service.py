from typing import Dict, Any
from backend.services.reverse_logistics_engine import ReverseLogisticsEngine
from backend.utils.logger import logger

class ReverseLogisticsService:
    """Service providing returns audits, recovery statistics, and AI recommendations."""

    @classmethod
    def get_reverse_logistics(cls, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Delegates to ReverseLogisticsEngine for full enterprise reverse intelligence.
        
        Args:
            filters: Global filters dictionary.
            
        Returns:
            Dict containing detailed reverse logistics payload.
        """
        logger.info("ReverseLogisticsService: Fetching reverse logistics intelligence payload.")
        return ReverseLogisticsEngine.evaluate_reverse_logistics_platform(filters)
