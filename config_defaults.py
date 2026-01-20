"""Default configuration values for BrainLink Client"""

from models.eeg_models import EegFaultModel, ConfigParams

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

# Default config file path
DEFAULT_CONFIG_PATH = "C:/BLconfig/config.json"

# Default history file path
DEFAULT_HISTORY_PATH = "C:/BLconfig/history.json"


def get_default_config() -> ConfigParams:
    """Get default configuration parameters"""
    return ConfigParams(
        eeg_fault=DEFAULT_BASE_FAULT,
        eeg_fault_multi=DEFAULT_MULTI_FAULT,
        multi_count=DEFAULT_MULTI_COUNT
    )
