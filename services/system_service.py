"""System service for cursor tracking"""

import pyautogui
from models.system_models import SystemInfo


class SystemService:
    """Service for tracking system cursor information"""

    def __init__(self):
        self.info = SystemInfo()

    def update_get_info(self) -> SystemInfo:
        """
        Update and get current cursor information
        
        Returns:
            SystemInfo with current cursor position
        """
        x, y = pyautogui.position()
        self.info.x = x
        self.info.y = y
        return self.info

    def run(self, info: SystemInfo) -> SystemInfo:
        """
        Update cursor movement delta
        
        Args:
            info: SystemInfo to update
            
        Returns:
            Updated SystemInfo
        """
        x, y = pyautogui.position()
        info.end_x = x
        info.end_y = y
        info.to_x = x - info.x
        info.to_y = y - info.y
        return info
