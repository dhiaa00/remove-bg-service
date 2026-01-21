"""
Logging configuration.
Provides structured logging with JSON format for production
and human-readable format for development.
"""
import logging
import sys
from app.config import get_settings


def setup_logging() -> None:
    """
    Configure application logging based on settings.
    
    In production (LOG_LEVEL=INFO or higher), uses a more structured format.
    In development (LOG_LEVEL=DEBUG), uses a simpler format for readability.
    """
    settings = get_settings()
    
    # Create formatter - simple but informative
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level.upper())
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("onnxruntime").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)
