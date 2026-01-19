"""Mouse control service"""

import pyautogui
import threading
from typing import Optional
from models.eeg_models import EegHistoryModel, ConfigParams


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

        if event_name and event_name != "stop" and is_use:
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

            if event == "ml":  # Move left
                pyautogui.moveTo(current_x - 1, current_y)
            elif event == "mr":  # Move right
                pyautogui.moveTo(current_x + 1, current_y)
            elif event == "md":  # Move down
                pyautogui.moveTo(current_x, current_y + 1)
            elif event == "mu":  # Move up
                pyautogui.moveTo(current_x, current_y - 1)
        except Exception as e:
            print(f"Error moving mouse: {e}")

    def stop(self):
        """Stop all mouse movements"""
        self._stop_flag = True
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
