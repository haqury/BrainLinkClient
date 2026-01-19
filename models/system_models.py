"""System information models"""

from dataclasses import dataclass


@dataclass
class SystemInfo:
    """Model for system cursor information"""
    x: int = 0
    y: int = 0
    to_x: int = 0
    to_y: int = 0
    end_x: int = 0
    end_y: int = 0

    def is_use_mouse(self) -> bool:
        """Check if mouse is being used"""
        return self.to_x == 0 and self.to_y == 0

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'x': self.x,
            'y': self.y,
            'to_x': self.to_x,
            'to_y': self.to_y,
            'end_x': self.end_x,
            'end_y': self.end_y
        }
