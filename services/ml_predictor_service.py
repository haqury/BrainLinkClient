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
            try:
                loaded = self.trainer.load_model()
                if loaded:
                    logger.info("Loaded existing ML model from file")
                else:
                    logger.info("No existing ML model found")
            except Exception as e:
                logger.error(f"Error loading model: {e}", exc_info=True)
                self.trainer.is_trained = False
                self.trainer.model = None
        
        # Verify model if it claims to be trained
        if self.trainer.is_trained:
            if self.trainer.model is None:
                logger.warning("Model claims to be trained but model is None - resetting")
                self.trainer.is_trained = False
            elif not hasattr(self.trainer.model, 'predict'):
                logger.warning("Model does not have predict method - resetting")
                self.trainer.is_trained = False
                self.trainer.model = None
        
        logger.info(f"MLPredictorService initialized (model trained: {self.trainer.is_trained}, model ready: {self.is_ready()})")
    
    def predict(self, eeg_data: BrainLinkModel) -> Optional[MLPrediction]:
        """
        Predict event from EEG data
        
        Args:
            eeg_data: BrainLink EEG data
            
        Returns:
            Prediction result or None if model not trained or error occurred
        """
        # Check if model is available and trained
        if not self.trainer.is_trained:
            logger.debug("Model not trained - cannot predict")
            return None
        
        if self.trainer.model is None:
            logger.warning("Model is None - cannot predict")
            return None
        
        try:
            # Convert EEG data to features
            features = self._eeg_to_features(eeg_data)
            
            # Validate features
            if not features or len(features) == 0:
                logger.warning("Empty features - cannot predict")
                return None
            
            # Check for NaN or invalid values
            if any(not isinstance(f, (int, float)) or (isinstance(f, float) and (np.isnan(f) or np.isinf(f))) for f in features):
                logger.warning(f"Invalid features detected: {features}")
                return None
            
            # Predict
            X = np.array([features])
            
            # Check if model has predict method
            if not hasattr(self.trainer.model, 'predict'):
                logger.error("Model does not have predict method")
                return None
            
            predicted_class = self.trainer.model.predict(X)[0]
            
            # Check if model has predict_proba method
            if not hasattr(self.trainer.model, 'predict_proba'):
                logger.warning("Model does not have predict_proba method - using default confidence")
                # Apply ml/mr inversion if enabled
                final_event = str(predicted_class)
                if self.config.invert_ml_mr:
                    if final_event == "ml":
                        final_event = "mr"
                        logger.debug(f"Inverted ml -> mr")
                    elif final_event == "mr":
                        final_event = "ml"
                        logger.debug(f"Inverted mr -> ml")
                # Return prediction with default confidence
                return MLPrediction(
                    predicted_event=final_event,
                    confidence=1.0,
                    probabilities={final_event: 1.0}
                )
            
            probabilities = self.trainer.model.predict_proba(X)[0]
            
            # Validate probabilities
            if probabilities is None or len(probabilities) == 0:
                logger.warning("Empty probabilities - cannot create prediction")
                return None
            
            # Get class labels
            if not hasattr(self.trainer.model, 'classes_'):
                logger.warning("Model does not have classes_ attribute - using indices")
                classes = [str(i) for i in range(len(probabilities))]
            else:
                classes = self.trainer.model.classes_
            
            # Validate classes
            if classes is None or len(classes) == 0:
                logger.warning("Empty classes - cannot create prediction")
                return None
            
            # Ensure classes and probabilities match
            if len(classes) != len(probabilities):
                logger.error(f"Classes and probabilities length mismatch: {len(classes)} vs {len(probabilities)}")
                return None
            
            # Create probability dictionary
            prob_dict = {str(cls): float(prob) for cls, prob in zip(classes, probabilities)}
            
            # Get confidence (max probability)
            confidence = float(max(probabilities))
            
            # Validate confidence
            if confidence < 0 or confidence > 1:
                logger.warning(f"Invalid confidence value: {confidence}")
                confidence = max(0.0, min(1.0, confidence))
            
            # Apply ml/mr inversion if enabled
            final_event = str(predicted_class)
            if self.config.invert_ml_mr:
                if final_event == "ml":
                    final_event = "mr"
                    logger.debug(f"Inverted ml -> mr")
                elif final_event == "mr":
                    final_event = "ml"
                    logger.debug(f"Inverted mr -> ml")
            
            prediction = MLPrediction(
                predicted_event=final_event,
                confidence=confidence,
                probabilities=prob_dict
            )
            
            logger.debug(f"ML Prediction: {predicted_class} -> {final_event} (confidence: {confidence:.2f}, probabilities: {prob_dict})")
            
            return prediction
        
        except AttributeError as e:
            logger.error(f"Attribute error during prediction: {e}", exc_info=True)
            return None
        except ValueError as e:
            logger.error(f"Value error during prediction: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Unexpected error during prediction: {e}", exc_info=True)
            return None
    
    def _eeg_to_features(self, eeg_data: BrainLinkModel) -> list:
        """Convert EEG data to weighted feature vector"""
        raw = {
            "attention": float(eeg_data.attention),
            "meditation": float(eeg_data.meditation),
            "delta": float(eeg_data.delta),
            "theta": float(eeg_data.theta),
            "low_alpha": float(eeg_data.low_alpha),
            "high_alpha": float(eeg_data.high_alpha),
            "low_beta": float(eeg_data.low_beta),
            "high_beta": float(eeg_data.high_beta),
            "low_gamma": float(eeg_data.low_gamma),
            "high_gamma": float(eeg_data.high_gamma),
        }
        weights = getattr(self.config, "feature_weights", {}) or {}
        ordered = MLTrainingData.feature_names()
        return [raw[name] * float(weights.get(name, 1.0)) for name in ordered]
    
    def is_ready(self) -> bool:
        """
        Check if predictor is ready to make predictions
        
        Returns:
            True if model is trained, loaded, and has required methods
        """
        if not self.trainer.is_trained:
            return False
        
        if self.trainer.model is None:
            return False
        
        # Check if model has required methods
        if not hasattr(self.trainer.model, 'predict'):
            logger.warning("Model does not have predict method")
            return False
        
        return True
