"""EEG data models for BrainLink Client"""

from dataclasses import dataclass, field
from typing import List, Optional
import json


@dataclass
class BrainLinkModel:
    """Model for BrainLink EEG data"""
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

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'attention': self.attention,
            'meditation': self.meditation,
            'signal': self.signal,
            'delta': self.delta,
            'theta': self.theta,
            'low_alpha': self.low_alpha,
            'high_alpha': self.high_alpha,
            'low_beta': self.low_beta,
            'high_beta': self.high_beta,
            'low_gamma': self.low_gamma,
            'high_gamma': self.high_gamma
        }


@dataclass
class BrainLinkExtendModel:
    """Extended BrainLink data model"""
    ap: int = 0
    electric: int = 0
    version: str = ""
    temperature: float = 0.0
    heart_rate: int = 0

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'ap': self.ap,
            'electric': self.electric,
            'version': self.version,
            'temperature': self.temperature,
            'heart_rate': self.heart_rate
        }


@dataclass
class EegHistoryModel:
    """Model for EEG history records"""
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

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'attention': self.attention,
            'meditation': self.meditation,
            'signal': self.signal,
            'delta': self.delta,
            'theta': self.theta,
            'low_alpha': self.low_alpha,
            'high_alpha': self.high_alpha,
            'low_beta': self.low_beta,
            'high_beta': self.high_beta,
            'low_gamma': self.low_gamma,
            'high_gamma': self.high_gamma,
            'event_name': self.event_name
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Create from dictionary"""
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
            high_gamma=data.get('high_gamma', 0),
            event_name=data.get('event_name', '')
        )


@dataclass
class EegFaultModel:
    """Model for EEG fault tolerance configuration"""
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

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'attention': self.attention,
            'meditation': self.meditation,
            'signal': self.signal,
            'delta': self.delta,
            'theta': self.theta,
            'low_alpha': self.low_alpha,
            'high_alpha': self.high_alpha,
            'low_beta': self.low_beta,
            'high_beta': self.high_beta,
            'low_gamma': self.low_gamma,
            'high_gamma': self.high_gamma
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Create from dictionary"""
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
