"""ML Prediction Service for real-time EEG event detection"""

import logging
from typing import Optional
import numpy as np

from pybrainlink import BrainLinkModel
from models.ml_models import MLConfig, MLPrediction, MLTrainingData
from services.ml_trainer_service import MLTrainerService

logger = logging.getLogger(__name__)


class MLPredictorService:
    """Service for predicting events using trained ML model"""
    
    def __init__(self, trainer: Optional[MLTrainerService] = None):
        """
        Initialize ML predictor service
        
        Args:
            trainer: ML trainer service (for accessing trained model)
        """
        self.trainer = trainer or MLTrainerService()
        self.config = self.trainer.config
        
        # Try to load existing model
        if not self.trainer.is_trained:
            self.trainer.load_model()
        
        logger.info(f"MLPredictorService initialized (model trained: {self.trainer.is_trained})")
    
    def predict(self, eeg_data: BrainLinkModel) -> Optional[MLPrediction]:
        """
        Predict event from EEG data
        
        Args:
            eeg_data: BrainLink EEG data
            
        Returns:
            Prediction result or None if model not trained
        """
        if not self.trainer.is_trained or self.trainer.model is None:
            logger.warning("Model not trained - cannot predict")
            return None
        
        try:
            # Convert EEG data to features
            features = self._eeg_to_features(eeg_data)
            
            # Predict
            X = np.array([features])
            predicted_class = self.trainer.model.predict(X)[0]
            probabilities = self.trainer.model.predict_proba(X)[0]
            
            # Get class labels
            classes = self.trainer.model.classes_
            
            # Create probability dictionary
            prob_dict = {cls: float(prob) for cls, prob in zip(classes, probabilities)}
            
            # Get confidence (max probability)
            confidence = float(max(probabilities))
            
            prediction = MLPrediction(
                predicted_event=predicted_class,
                confidence=confidence,
                probabilities=prob_dict
            )
            
            logger.debug(f"Predicted: {predicted_class} (confidence: {confidence:.2f})")
            
            return prediction
        
        except Exception as e:
            logger.error(f"Error during prediction: {e}", exc_info=True)
            return None
    
    def _eeg_to_features(self, eeg_data: BrainLinkModel) -> list:
        """Convert EEG data to feature vector"""
        return [
            float(eeg_data.attention),
            float(eeg_data.meditation),
            float(eeg_data.delta),
            float(eeg_data.theta),
            float(eeg_data.low_alpha),
            float(eeg_data.high_alpha),
            float(eeg_data.low_beta),
            float(eeg_data.high_beta),
            float(eeg_data.low_gamma),
            float(eeg_data.high_gamma)
        ]
    
    def is_ready(self) -> bool:
        """Check if predictor is ready to make predictions"""
        return self.trainer.is_trained and self.trainer.model is not None
