"""Mouse control service"""

import logging
import pyautogui
import threading
from typing import Optional
from models.eeg_models import EegHistoryModel, ConfigParams
from models.event_types import EventType

logger = logging.getLogger(__name__)


class MouseService:
    """Service for controlling mouse movements based on EEG events"""

    def __init__(self):
        self._timer: Optional[threading.Timer] = None
        self._stop_flag = False
        self._current_event = ""
        pyautogui.FAILSAFE = False  # Disable failsafe for corners

    def play(
        self,
        eeg_data: EegHistoryModel,
        config: ConfigParams,
        event_name: str,
        is_use: bool
    ):
        """
        Execute mouse action based on event
        
        Args:
            eeg_data: Current EEG data
            config: Configuration parameters
            event_name: Event name (ml, mr, mu, md, stop)
            is_use: Whether to use keyboard control
        """
        # Stop previous timer if exists
        if self._timer is not None:
            self._stop_flag = True
            self._timer.cancel()
            self._timer = None

        if event_name and event_name != EventType.STOP.value and is_use:
            self._stop_flag = False
            self._current_event = event_name
            self._start_continuous_movement()

    def _start_continuous_movement(self):
        """Start continuous mouse movement"""
        if not self._stop_flag:
            self._play_key(self._current_event)
            self._timer = threading.Timer(0.01, self._start_continuous_movement)
            self._timer.start()

    def _play_key(self, event: str):
        """
        Execute mouse movement based on event
        
        Args:
            event: Event name (ml=left, mr=right, mu=up, md=down)
        """
        try:
            current_x, current_y = pyautogui.position()

            if event == EventType.MOVE_LEFT.value:  # Move left
                pyautogui.moveTo(current_x - 1, current_y)
            elif event == EventType.MOVE_RIGHT.value:  # Move right
                pyautogui.moveTo(current_x + 1, current_y)
            elif event == EventType.MOVE_DOWN.value:  # Move down
                pyautogui.moveTo(current_x, current_y + 1)
            elif event == EventType.MOVE_UP.value:  # Move up
                pyautogui.moveTo(current_x, current_y - 1)
        except Exception as e:
            logger.error(f"Error moving mouse: {e}", exc_info=True)

    def stop(self):
        """Stop all mouse movements"""
        self._stop_flag = True
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
