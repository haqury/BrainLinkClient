"""Utility functions for getting application base directory"""

import sys
import os
from pathlib import Path


def get_app_base_dir() -> Path:
    """
    Get the base directory for the application.
    
    In exe (frozen): returns directory where exe is located
    In normal Python: returns current working directory
    
    Returns:
        Path to base directory
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        # sys.executable is path to exe, so get its directory
        return Path(sys.executable).parent
    else:
        # Running as Python script
        # Use current working directory (where script is run from)
        return Path.cwd()


def get_config_dir() -> Path:
    """
    Get directory for config files.
    
    Returns:
        Path to config directory (app_base_dir/config)
    """
    base = get_app_base_dir()
    config_dir = base / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_logs_dir() -> Path:
    """
    Get directory for log files.
    
    Returns:
        Path to logs directory (app_base_dir/logs)
    """
    base = get_app_base_dir()
    logs_dir = base / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def get_models_dir() -> Path:
    """
    Get directory for ML model files.
    
    Returns:
        Path to models directory (app_base_dir/models_ml)
    """
    base = get_app_base_dir()
    models_dir = base / "models_ml"
    models_dir.mkdir(parents=True, exist_ok=True)
    return models_dir


def get_data_dir() -> Path:
    """
    Get directory for data files (history, etc.).
    
    Returns:
        Path to data directory (app_base_dir/data)
    """
    base = get_app_base_dir()
    data_dir = base / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir
