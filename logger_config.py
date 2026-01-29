"""Logging configuration for BrainLink Client"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logging(log_level=logging.INFO):
    """
    Configure logging for the application.
    
    Creates both console and file handlers with proper formatting.
    Log files are stored in app_base_dir/logs/
    
    Args:
        log_level: Logging level (default: INFO)
    """
    from utils.path_utils import get_logs_dir
    
    # Get logs directory (relative to exe or current dir)
    log_dir = get_logs_dir()
    
    # Create log filename with timestamp
    log_file = log_dir / f"brainlink_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)  # File gets everything
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Suppress verbose logs from external libraries
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('bleak').setLevel(logging.WARNING)
    
    root_logger.info("=" * 60)
    root_logger.info("BrainLink Client logging initialized")
    root_logger.info(f"Log file: {log_file}")
    root_logger.info("=" * 60)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Module name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
