"""ML Training Service for EEG event prediction"""

import logging
import json
import pickle
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from models.ml_models import MLTrainingData, MLConfig, MLPrediction
from models.event_types import EventType

logger = logging.getLogger(__name__)


class MLTrainerService:
    """Service for training ML models on EEG data"""
    
    def __init__(self, config: Optional[MLConfig] = None):
        """
        Initialize ML trainer service
        
        Args:
            config: ML configuration
        """
        self.config = config or MLConfig()
        self.model = None
        self.training_data: List[MLTrainingData] = []
        self.is_trained = False
        
        # Load existing training data if available
        self._load_training_data()
        
        logger.info("MLTrainerService initialized")
    
    def add_training_sample(self, data: MLTrainingData):
        """
        Add a training sample
        
        Args:
            data: Training data sample
        """
        self.training_data.append(data)
        logger.debug(f"Added training sample: event={data.event}, features={len(data.to_features())}")
    
    def save_training_data(self):
        """Save training data to file"""
        try:
            path = Path(self.config.training_data_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to JSON-serializable format
            data_list = []
            for sample in self.training_data:
                data_list.append({
                    'attention': sample.attention,
                    'meditation': sample.meditation,
                    'delta': sample.delta,
                    'theta': sample.theta,
                    'low_alpha': sample.low_alpha,
                    'high_alpha': sample.high_alpha,
                    'low_beta': sample.low_beta,
                    'high_beta': sample.high_beta,
                    'low_gamma': sample.low_gamma,
                    'high_gamma': sample.high_gamma,
                    'event': sample.event,
                    'timestamp': sample.timestamp.isoformat()
                })
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data_list, f, indent=2)
            
            logger.info(f"Saved {len(self.training_data)} training samples to {path}")
        
        except Exception as e:
            logger.error(f"Error saving training data: {e}", exc_info=True)
    
    def _load_training_data(self):
        """Load training data from file"""
        try:
            path = Path(self.config.training_data_path)
            if not path.exists():
                logger.info("No existing training data found")
                return
            
            with open(path, 'r', encoding='utf-8') as f:
                data_list = json.load(f)
            
            self.training_data = []
            for item in data_list:
                sample = MLTrainingData(
                    attention=item['attention'],
                    meditation=item['meditation'],
                    delta=item['delta'],
                    theta=item['theta'],
                    low_alpha=item['low_alpha'],
                    high_alpha=item['high_alpha'],
                    low_beta=item['low_beta'],
                    high_beta=item['high_beta'],
                    low_gamma=item['low_gamma'],
                    high_gamma=item['high_gamma'],
                    event=item['event'],
                    timestamp=datetime.fromisoformat(item['timestamp'])
                )
                self.training_data.append(sample)
            
            logger.info(f"Loaded {len(self.training_data)} training samples from {path}")
        
        except Exception as e:
            logger.error(f"Error loading training data: {e}", exc_info=True)
    
    def get_training_stats(self) -> Dict[str, int]:
        """
        Get statistics about training data
        
        Returns:
            Dictionary with event counts
        """
        stats = {}
        for event_type in EventType:
            count = sum(1 for sample in self.training_data if sample.event == event_type.value)
            stats[event_type.value] = count
        
        return stats
    
    def import_from_history(self, history_records: List) -> Tuple[int, int]:
        """
        Import training data from history records
        
        Args:
            history_records: List of EegHistoryModel records
        
        Returns:
            Tuple of (imported_count, skipped_count)
        """
        imported = 0
        skipped = 0
        
        for record in history_records:
            # Skip records without event
            if not hasattr(record, 'event_name') or not record.event_name:
                skipped += 1
                continue
            
            # Skip records with invalid events
            valid_events = [e.value for e in EventType]
            if record.event_name not in valid_events:
                skipped += 1
                continue
            
            try:
                # Convert history record to training data
                training_sample = MLTrainingData(
                    attention=record.attention,
                    meditation=record.meditation,
                    delta=record.delta,
                    theta=record.theta,
                    low_alpha=record.low_alpha,
                    high_alpha=record.high_alpha,
                    low_beta=record.low_beta,
                    high_beta=record.high_beta,
                    low_gamma=record.low_gamma,
                    high_gamma=record.high_gamma,
                    event=record.event_name
                )
                
                self.training_data.append(training_sample)
                imported += 1
                
            except Exception as e:
                logger.warning(f"Failed to import record: {e}")
                skipped += 1
        
        logger.info(f"Imported {imported} samples from history, skipped {skipped}")
        return imported, skipped
    
    def can_train(self) -> Tuple[bool, str]:
        """
        Check if model can be trained
        
        Returns:
            (can_train, reason)
        """
        if len(self.training_data) == 0:
            return False, "No training data available"
        
        stats = self.get_training_stats()
        min_samples = self.config.min_samples_per_class
        
        for event, count in stats.items():
            if count < min_samples:
                return False, f"Not enough samples for '{event}': {count} < {min_samples}"
        
        return True, "Ready to train"
    
    def train_model(self) -> Dict[str, any]:
        """
        Train ML model on collected data
        
        Returns:
            Training metrics and results
        """
        logger.info("Starting model training...")
        
        # Check if can train
        can_train, reason = self.can_train()
        if not can_train:
            logger.error(f"Cannot train model: {reason}")
            raise ValueError(reason)
        
        # Prepare data
        X = np.array([sample.to_features() for sample in self.training_data])
        y = np.array([sample.event for sample in self.training_data])
        
        logger.info(f"Training data shape: X={X.shape}, y={y.shape}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=self.config.test_size,
            random_state=self.config.random_state,
            stratify=y
        )
        
        # Create model
        if self.config.model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=self.config.n_estimators,
                max_depth=self.config.max_depth,
                random_state=self.config.random_state
            )
        elif self.config.model_type == 'svm':
            self.model = SVC(
                kernel='rbf',
                probability=True,
                random_state=self.config.random_state
            )
        elif self.config.model_type == 'neural_network':
            self.model = MLPClassifier(
                hidden_layer_sizes=(100, 50),
                max_iter=500,
                random_state=self.config.random_state
            )
        else:
            raise ValueError(f"Unknown model type: {self.config.model_type}")
        
        # Train
        logger.info(f"Training {self.config.model_type} model...")
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)
        
        train_accuracy = accuracy_score(y_train, y_pred_train)
        test_accuracy = accuracy_score(y_test, y_pred_test)
        
        logger.info(f"Training accuracy: {train_accuracy:.3f}")
        logger.info(f"Testing accuracy: {test_accuracy:.3f}")
        
        # Save model
        self.save_model()
        
        self.is_trained = True
        
        # Return metrics
        metrics = {
            'train_accuracy': train_accuracy,
            'test_accuracy': test_accuracy,
            'n_samples': len(self.training_data),
            'n_features': X.shape[1],
            'model_type': self.config.model_type,
            'classification_report': classification_report(y_test, y_pred_test),
            'confusion_matrix': confusion_matrix(y_test, y_pred_test).tolist()
        }
        
        logger.info("Model training completed successfully")
        return metrics
    
    def save_model(self):
        """Save trained model to file"""
        if self.model is None:
            logger.warning("No model to save")
            return
        
        try:
            path = Path(self.config.model_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'wb') as f:
                pickle.dump(self.model, f)
            
            logger.info(f"Model saved to {path}")
        
        except Exception as e:
            logger.error(f"Error saving model: {e}", exc_info=True)
    
    def load_model(self) -> bool:
        """
        Load trained model from file
        
        Returns:
            True if model loaded successfully
        """
        try:
            path = Path(self.config.model_path)
            if not path.exists():
                logger.info("No saved model found")
                return False
            
            with open(path, 'rb') as f:
                self.model = pickle.load(f)
            
            self.is_trained = True
            logger.info(f"Model loaded from {path}")
            return True
        
        except Exception as e:
            logger.error(f"Error loading model: {e}", exc_info=True)
            return False
    
    def clear_training_data(self):
        """Clear all training data"""
        self.training_data.clear()
        logger.info("Training data cleared")
