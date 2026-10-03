"""Default configuration values for BrainLink Client"""

import json
import logging
from pathlib import Path
from typing import Optional, Tuple

from models.eeg_models import EegFaultModel, ConfigParams

logger = logging.getLogger(__name__)

# Default base fault tolerance values (from original BrainLinkConnect)
DEFAULT_BASE_FAULT = EegFaultModel(
    attention=5,
    meditation=10,
    signal=0,
    delta=300,
    theta=300,
    low_alpha=0,
    high_alpha=0,
    low_beta=0,
    high_beta=0,
    low_gamma=0,
    high_gamma=0
)

# Default multi-level multiplier values
DEFAULT_MULTI_FAULT = EegFaultModel(
    attention=1,
    meditation=1,
    signal=1,
    delta=3,
    theta=3,
    low_alpha=3,
    high_alpha=3,
    low_beta=3,
    high_beta=3,
    low_gamma=3,
    high_gamma=3
)

# Default multi count
DEFAULT_MULTI_COUNT = 1

# Default config file paths (will be resolved at runtime via path_utils)
# These are relative to app base directory
DEFAULT_CONFIG_PATH = None  # Will be set dynamically
DEFAULT_HISTORY_PATH = None  # Will be set dynamically


def get_default_config_path() -> str:
    """Get default config file path (relative to app base directory)"""
    from utils.path_utils import get_config_dir
    return str(get_config_dir() / "config.json")


def get_default_history_path() -> str:
    """Get default history file path (relative to app base directory)"""
    from utils.path_utils import get_data_dir
    return str(get_data_dir() / "history.json")


def get_default_config() -> ConfigParams:
    """Get default configuration parameters"""
    config = ConfigParams(
        eeg_fault=DEFAULT_BASE_FAULT,
        eeg_fault_multi=DEFAULT_MULTI_FAULT,
        multi_count=DEFAULT_MULTI_COUNT
    )
    # get_event_name_by() matches against eeg_faults — must be populated at startup
    config.eeg_faults = [DEFAULT_BASE_FAULT]
    return config


def _parse_fault_config_data(
    data: dict,
) -> Tuple[EegFaultModel, EegFaultModel, int]:
    """Parse full or legacy fault-config JSON into models."""
    if "base_fault" in data:
        base = EegFaultModel.from_dict(data["base_fault"])
        multi = EegFaultModel.from_dict(data.get("multi_fault", {}))
        multi_count = int(data.get("multi_count", DEFAULT_MULTI_COUNT) or DEFAULT_MULTI_COUNT)
    else:
        # Legacy: file contains only base fault fields
        base = EegFaultModel.from_dict(data)
        multi = DEFAULT_MULTI_FAULT
        multi_count = DEFAULT_MULTI_COUNT
    return base, multi, max(1, multi_count)


def load_fault_config(
    path: Optional[str] = None,
) -> Optional[Tuple[EegFaultModel, EegFaultModel, int]]:
    """
    Load persisted fault config from disk.

    Prefers config/config.json; if missing, falls back to config/def_conf.json.
    Returns (base, multi, multi_count) or None if nothing found.
    """
    from utils.path_utils import get_config_dir

    candidates = []
    if path:
        candidates.append(Path(path))
    else:
        config_dir = get_config_dir()
        candidates.append(config_dir / "config.json")
        candidates.append(config_dir / "def_conf.json")

    for file_path in candidates:
        if not file_path.exists():
            continue
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            parsed = _parse_fault_config_data(data)
            logger.info(
                "Loaded fault config from %s (multi_count=%s)",
                file_path,
                parsed[2],
            )
            return parsed
        except Exception as e:
            logger.error("Error loading fault config from %s: %s", file_path, e, exc_info=True)
    return None


def save_fault_config(
    base: EegFaultModel,
    multi: EegFaultModel,
    multi_count: int,
    path: Optional[str] = None,
) -> bool:
    """Persist fault config to config/config.json (or given path)."""
    file_path = Path(path) if path else Path(get_default_config_path())
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "base_fault": base.to_dict(),
            "multi_fault": multi.to_dict(),
            "multi_count": int(multi_count),
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        logger.info("Saved fault config to %s (multi_count=%s)", file_path, multi_count)
        return True
    except Exception as e:
        logger.error("Error saving fault config to %s: %s", file_path, e, exc_info=True)
        return False
