"""Machine Learning models for EEG event prediction"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class MLTrainingData:
    """Training data sample for ML model"""
    # EEG features
    attention: int
    meditation: int
    delta: int
    theta: int
    low_alpha: int
    high_alpha: int
    low_beta: int
    high_beta: int
    low_gamma: int
    high_gamma: int
    
    # Target event
    event: str  # 'ml', 'mr', 'mu', 'md', 'stop'
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_features(self) -> List[float]:
        """Convert to feature vector for ML model"""
        return [
            float(self.attention),
            float(self.meditation),
            float(self.delta),
            float(self.theta),
            float(self.low_alpha),
            float(self.high_alpha),
            float(self.low_beta),
            float(self.high_beta),
            float(self.low_gamma),
            float(self.high_gamma)
        ]
    
    @staticmethod
    def feature_names() -> List[str]:
        """Get feature names for the model"""
        return [
            'attention',
            'meditation',
            'delta',
            'theta',
            'low_alpha',
            'high_alpha',
            'low_beta',
            'high_beta',
            'low_gamma',
            'high_gamma'
        ]


@dataclass
class MLConfig:
    """Configuration for ML model"""
    # Model settings
    model_type: str = 'random_forest'  # 'random_forest', 'svm', 'neural_network'
    n_estimators: int = 100  # For RandomForest
    max_depth: Optional[int] = 10
    random_state: int = 42
    
    # Training settings
    test_size: float = 0.2
    min_samples_per_class: int = 10
    min_classes_required: int = 2  # Minimum number of event classes needed for training
    
    # Auto-training settings
    auto_train_enabled: bool = True  # Enable automatic training when new samples added
    auto_train_min_new_samples: int = 5  # Minimum new samples before auto-training
    
    # Prediction settings
    confidence_threshold: float = 0.6  # Minimum confidence for prediction
    invert_ml_mr: bool = False  # Invert ml/mr predictions (fix if model predicts backwards)
    
    # File paths
    model_path: str = "models_ml/brainlink_classifier.pkl"
    training_data_path: str = "training_data/ml_training_data.json"
    
    def __post_init__(self):
        """Validate configuration"""
        if not 0 < self.test_size < 1:
            raise ValueError(f"test_size must be between 0 and 1, got {self.test_size}")
        
        if not 0 < self.confidence_threshold <= 1:
            raise ValueError(f"confidence_threshold must be between 0 and 1, got {self.confidence_threshold}")
        
        if self.min_samples_per_class < 1:
            raise ValueError(f"min_samples_per_class must be >= 1, got {self.min_samples_per_class}")


@dataclass
class MLPrediction:
    """Prediction result from ML model"""
    predicted_event: str
    confidence: float
    probabilities: dict  # {event: probability}
    
    def is_confident(self, threshold: float) -> bool:
        """Check if prediction confidence is above threshold"""
        return self.confidence >= threshold
