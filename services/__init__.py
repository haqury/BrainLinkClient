"""Services package for BrainLink Client"""

from .history_service import HistoryService
from .head_tracker_service import HeadTracker
from .mouse_service import MouseService
from .system_service import SystemService
from .device_simulator import DeviceSimulator, SimulatorController

# Note: BluetoothService is now replaced by pybrainlink.BrainLinkDevice

__all__ = [
    'HistoryService',
    'HeadTracker',
    'MouseService',
    'SystemService',
    'DeviceSimulator',
    'SimulatorController'
]
