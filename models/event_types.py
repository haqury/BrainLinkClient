"""Event types enumeration for EEG events"""

from enum import Enum


class EventType(str, Enum):
    """Enumeration of possible EEG event types"""
    
    MOVE_LEFT = "ml"
    MOVE_RIGHT = "mr"
    MOVE_UP = "mu"
    MOVE_DOWN = "md"
    STOP = "stop"
    
    def __str__(self) -> str:
        """Return the event value as string"""
        return self.value
    
    @classmethod
    def from_string(cls, value: str) -> 'EventType':
        """
        Create EventType from string value.
        
        Args:
            value: String representation of event type
            
        Returns:
            EventType instance
            
        Raises:
            ValueError: If value is not a valid event type
        """
        try:
            return cls(value)
        except ValueError:
            raise ValueError(f"Invalid event type: {value}. "
                           f"Valid types: {', '.join([e.value for e in cls])}")
    
    @classmethod
    def all_types(cls) -> list['EventType']:
        """Return list of all event types"""
        return list(cls)
