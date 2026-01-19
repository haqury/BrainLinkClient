"""Gyroscope data models"""

from dataclasses import dataclass


@dataclass
class GyroHistory:
    """Model for gyroscope history data"""
    x_value: int = 0
    y_value: int = 0
    z_value: int = 0

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'x_value': self.x_value,
            'y_value': self.y_value,
            'z_value': self.z_value
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Create from dictionary"""
        return cls(
            x_value=data.get('x_value', 0),
            y_value=data.get('y_value', 0),
            z_value=data.get('z_value', 0)
        )
