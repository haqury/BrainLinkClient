"""Head tracker service for gyroscope data processing"""

import numpy as np
from typing import Optional


class HeadTracker:
    """Service for tracking head movements using gyroscope data"""

    def __init__(self):
        self._initial_euler: Optional[np.ndarray] = None
        self._is_calibrated = False

    def process_raw_data(self, x: int, y: int, z: int) -> np.ndarray:
        """
        Process raw gyroscope data into euler angles
        
        Args:
            x, y, z: Raw gyroscope values
            
        Returns:
            numpy array with [pitch, yaw, roll] in degrees
        """
        # Convert raw values to angles (adjust based on your gyroscope)
        pitch = (x / 32768.0) * 90.0  # Example for ±90°
        yaw = (y / 32768.0) * 90.0
        roll = (z / 32768.0) * 90.0
        
        return np.array([pitch, yaw, roll])

    def calibrate(self, x: int, y: int, z: int):
        """
        Calibrate the initial head position
        
        Args:
            x, y, z: Raw gyroscope values at calibration
        """
        self._initial_euler = self.process_raw_data(x, y, z)
        self._is_calibrated = True
        print(f"Head tracker calibrated: {self._initial_euler}")

    def de_calibrate(self):
        """Reset calibration"""
        self._is_calibrated = False
        self._initial_euler = None
        print("Head tracker calibration reset")

    def is_calibrated(self) -> bool:
        """Check if tracker is calibrated"""
        return self._is_calibrated

    def get_direction_key(self, x: int, y: int, z: int) -> str:
        """
        Get direction based on head movement
        
        Args:
            x, y, z: Current gyroscope values
            
        Returns:
            Direction string: 'up', 'down', 'left', 'right', or ''
        """
        if not self._is_calibrated:
            return "not_calibrated"

        current_euler = self.process_raw_data(x, y, z)
        delta = current_euler - self._initial_euler

        # Threshold for movement detection (adjust for sensitivity)
        threshold = 0.1  # 30 degrees in original, but adjusted

        # Check each axis
        if delta[0] > threshold:
            return "down"
        elif delta[0] < -threshold:
            return "up"
        elif delta[1] > threshold:
            return "right"
        elif delta[1] < -threshold:
            return "left"

        return ""
