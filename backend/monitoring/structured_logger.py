"""Centralized structured logging service formatting logs as standardized JSON lines."""

import json
import logging
import time
from typing import Any, Dict
from backend.utils.logger import logger as base_logger


class StructuredLogger:
    """Wrapper that outputs JSON structured log lines to support log shippers and analysis tools."""

    @classmethod
    def log(cls, level: str, message: str, context: Dict[str, Any] = None) -> None:
        """Outputs a structured JSON log entry.

        Args:
            level: INFO, WARNING, ERROR, CRITICAL.
            message: Standard string description message.
            context: Key-value context payload dict.
        """
        if context is None:
            context = {}

        log_data = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "level": level.upper(),
            "message": message,
            "context": context
        }

        json_str = json.dumps(log_data)
        
        # Log to base logger
        if level.upper() == "INFO":
            base_logger.info(json_str)
        elif level.upper() == "WARNING":
            base_logger.warning(json_str)
        elif level.upper() == "ERROR":
            base_logger.error(json_str)
        elif level.upper() == "CRITICAL":
            base_logger.critical(json_str)
        else:
            base_logger.info(json_str)

    @classmethod
    def info(cls, message: str, context: Dict[str, Any] = None) -> None:
        """Helper to log at INFO level."""
        cls.log("INFO", message, context)

    @classmethod
    def warning(cls, message: str, context: Dict[str, Any] = None) -> None:
        """Helper to log at WARNING level."""
        cls.log("WARNING", message, context)

    @classmethod
    def error(cls, message: str, context: Dict[str, Any] = None) -> None:
        """Helper to log at ERROR level."""
        cls.log("ERROR", message, context)
