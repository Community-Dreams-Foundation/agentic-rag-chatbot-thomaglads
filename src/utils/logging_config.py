"""Logging configuration for Codex.

Centralized logging setup with consistent formatting across the application.
"""

import logging
import sys
from typing import Optional


def setup_logging(
    level: Optional[str] = None,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """Setup logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR). Defaults to INFO.
        format_string: Custom format string. Uses default if None.
        
    Returns:
        Logger instance
    """
    # Get level from environment or use default
    log_level = level or "INFO"
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Default format
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format=format_string,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
        force=True,  # Override any existing configuration
    )
    
    # Get logger for codex
    logger = logging.getLogger("codex")
    logger.setLevel(numeric_level)
    
    return logger


# Create default logger instance
logger = setup_logging()
