"""EEG data models for BrainLink Client"""

import logging
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
import json

from .event_types import EventType

logger = logging.getLogger(__name__)


@dataclass
class BrainLinkModel:
    """Model for BrainLink EEG data with validation"""
    attention: int = 0
    meditation: int = 0
    signal: int = 0
    delta: int = 0
    theta: int = 0
    low_alpha: int = 0
    high_alpha: int = 0
    low_beta: int = 0
    high_beta: int = 0
    low_gamma: int = 0
    high_gamma: int = 0

    def __post_init__(self):
        """Validate data after initialization"""
        self._validate_range('attention', 0, 100)
        self._validate_range('meditation', 0, 100)
        self._validate_range('signal', 0, 200)
        
        # EEG bands are typically large values, allow up to 16777215 (0xFFFFFF)
        for field_name in ['delta', 'theta', 'low_alpha', 'high_alpha', 
                          'low_beta', 'high_beta', 'low_gamma', 'high_gamma']:
            self._validate_range(field_name, 0, 16777215)
    
    def _validate_range(self, field_name: str, min_val: int, max_val: int):
        """Validate that a field is within valid range"""
        value = getattr(self, field_name)
        if not isinstance(value, int):
            logger.warning(f"{field_name} is not an integer, converting: {value}")
            setattr(self, field_name, int(value))
            value = getattr(self, field_name)
        
        if not (min_val <= value <= max_val):
            logger.warning(f"{field_name} value {value} out of range [{min_val}, {max_val}], clamping")
            setattr(self, field_name, max(min_val, min(max_val, value)))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary using dataclasses.asdict()"""
        return asdict(self)


@dataclass
class BrainLinkExtendModel:
    """Extended BrainLink data model with validation"""
    ap: int = 0
    electric: int = 0
    version: str = ""
    temperature: float = 0.0
    heart_rate: int = 0

    def __post_init__(self):
        """Validate data after initialization"""
        # Validate AP (typically 0-100%)
        if not isinstance(self.ap, int):
            self.ap = int(self.ap)
        self.ap = max(0, min(100, self.ap))
        
        # Validate electric (battery, typically 0-100%)
        if not isinstance(self.electric, int):
            self.electric = int(self.electric)
        self.electric = max(0, min(100, self.electric))
        
        # Validate version is string
        if not isinstance(self.version, str):
            self.version = str(self.version)
        
        # Validate temperature (reasonable range for body temp: -10 to 60°C)
        if not isinstance(self.temperature, (int, float)):
            self.temperature = float(self.temperature)
        if not (-10 <= self.temperature <= 60):
            logger.warning(f"Temperature {self.temperature}°C out of reasonable range")
        
        # Validate heart rate (0-300 bpm)
        if not isinstance(self.heart_rate, int):
            self.heart_rate = int(self.heart_rate)
        if not (0 <= self.heart_rate <= 300):
            logger.warning(f"Heart rate {self.heart_rate} bpm out of reasonable range")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary using dataclasses.asdict()"""
        return asdict(self)


@dataclass
class EegHistoryModel:
    """Model for EEG history records with event type validation"""
    attention: int = 0
    meditation: int = 0
    signal: int = 0
    delta: int = 0
    theta: int = 0
    low_alpha: int = 0
    high_alpha: int = 0
    low_beta: int = 0
    high_beta: int = 0
    low_gamma: int = 0
    high_gamma: int = 0
    event_name: str = ""

    def __post_init__(self):
        """Validate data after initialization"""
        # Validate EEG values using same logic as BrainLinkModel
        self._validate_range('attention', 0, 100)
        self._validate_range('meditation', 0, 100)
        self._validate_range('signal', 0, 200)
        
        for field_name in ['delta', 'theta', 'low_alpha', 'high_alpha', 
                          'low_beta', 'high_beta', 'low_gamma', 'high_gamma']:
            self._validate_range(field_name, 0, 16777215)
        
        # Validate event_name is a valid EventType
        if self.event_name:
            try:
                EventType.from_string(self.event_name)
            except ValueError as e:
                logger.warning(f"Invalid event_name in EegHistoryModel: {e}")
    
    def _validate_range(self, field_name: str, min_val: int, max_val: int):
        """Validate that a field is within valid range"""
        value = getattr(self, field_name)
        if not isinstance(value, int):
            setattr(self, field_name, int(value))
            value = getattr(self, field_name)
        
        if not (min_val <= value <= max_val):
            setattr(self, field_name, max(min_val, min(max_val, value)))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary using dataclasses.asdict()"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EegHistoryModel':
        """
        Create from dictionary with validation.
        
        Args:
            data: Dictionary with EEG history data
            
        Returns:
            EegHistoryModel instance
        """
        # Support both new (snake_case) and legacy (CamelCase) keys
        return cls(
            attention=data.get('attention', data.get('Attention', 0)),
            meditation=data.get('meditation', data.get('Meditation', 0)),
            signal=data.get('signal', data.get('Signal', 0)),
            delta=data.get('delta', data.get('Delta', 0)),
            theta=data.get('theta', data.get('Theta', 0)),
            low_alpha=data.get('low_alpha', data.get('LowAlpha', 0)),
            high_alpha=data.get('high_alpha', data.get('HighAlpha', 0)),
            low_beta=data.get('low_beta', data.get('LowBeta', 0)),
            high_beta=data.get('high_beta', data.get('HighBeta', 0)),
            low_gamma=data.get('low_gamma', data.get('LowGamma', 0)),
            high_gamma=data.get('high_gamma', data.get('HighGamma', 0)),
            event_name=data.get('event_name', data.get('EventName', ''))
        )


@dataclass
class EegFaultModel:
    """Model for EEG fault tolerance configuration with validation"""
    attention: int = 0
    meditation: int = 0
    signal: int = 0
    delta: int = 0
    theta: int = 0
    low_alpha: int = 0
    high_alpha: int = 0
    low_beta: int = 0
    high_beta: int = 0
    low_gamma: int = 0
    high_gamma: int = 0

    def __post_init__(self):
        """Validate fault tolerance values are non-negative"""
        for field_name in ['attention', 'meditation', 'signal', 'delta', 'theta',
                          'low_alpha', 'high_alpha', 'low_beta', 'high_beta',
                          'low_gamma', 'high_gamma']:
            value = getattr(self, field_name)
            if not isinstance(value, int):
                logger.warning(f"Fault tolerance {field_name} is not int, converting: {value}")
                setattr(self, field_name, int(value))
                value = getattr(self, field_name)
            
            if value < 0:
                logger.warning(f"Fault tolerance {field_name} is negative: {value}, setting to 0")
                setattr(self, field_name, 0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary using dataclasses.asdict()"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EegFaultModel':
        """
        Create from dictionary with validation.
        
        Args:
            data: Dictionary with fault tolerance data
            
        Returns:
            EegFaultModel instance
        """
        return cls(
            attention=data.get('attention', 0),
            meditation=data.get('meditation', 0),
            signal=data.get('signal', 0),
            delta=data.get('delta', 0),
            theta=data.get('theta', 0),
            low_alpha=data.get('low_alpha', 0),
            high_alpha=data.get('high_alpha', 0),
            low_beta=data.get('low_beta', 0),
            high_beta=data.get('high_beta', 0),
            low_gamma=data.get('low_gamma', 0),
            high_gamma=data.get('high_gamma', 0)
        )


@dataclass
class ConfigParams:
    """Configuration parameters"""
    eeg_fault: Optional[EegFaultModel] = None
    eeg_fault_multi: Optional[EegFaultModel] = None
    multi_count: int = 1
    eeg_faults: List[EegFaultModel] = field(default_factory=list)

    def __post_init__(self):
        if self.eeg_fault is None:
            self.eeg_fault = EegFaultModel()
        if self.eeg_fault_multi is None:
            self.eeg_fault_multi = EegFaultModel()
