"""Logging configuration for Change Management Analysis System."""

import logging
import logging.handlers
from pathlib import Path
from config.settings import settings


def setup_logging() -> logging.Logger:
    """
    Configure logging for the application.
    
    Logs to both console and file with appropriate formatting.
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger("IncidenceManagement")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    # Create logs directory if it doesn't exist
    Path(settings.LOGS_PATH).mkdir(exist_ok=True)

    # Log format
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s - %(name)s - %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# Global logger instance
logger = setup_logging()


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(f"IncidenceManagement.{name}")
