import logging
import os
from backend.config import LOGS_DIR

def setup_logger(name: str = "logistics_platform") -> logging.Logger:
    """Configures and returns a multi-handler logger (file & console)."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if setup_logger is called multiple times
    if logger.handlers:
        return logger

    # Formatters
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s"
    )

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    log_file = os.path.join(LOGS_DIR, "app.log")
    try:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Failed to initialize file logger at {log_file}: {e}")

    return logger

# Default platform-wide logger instance
logger = setup_logger()
