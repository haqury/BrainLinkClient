"""ML Training Service for EEG event prediction"""

import logging
import json
import pickle
import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from threading import Lock
import multiprocessing
from multiprocessing import Process, Queue

# Set multiprocessing start method for Windows compatibility
# This must be done before creating any Process objects
if sys.platform == 'win32':
    try:
        multiprocessing.set_start_method('spawn', force=True)
    except RuntimeError:
        # Already set, ignore
        pass

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from PyQt5.QtCore import QObject, pyqtSignal, QTimer

from models.ml_models import MLTrainingData, MLConfig, MLPrediction
from models.event_types import EventType

logger = logging.getLogger(__name__)


def _train_model_in_process(training_data_json: str, config_dict: dict, result_queue: Queue):
    """
    Train model in separate process (to avoid blocking UI)
    
    This function runs in a completely separate Python process,
    so it won't block the main UI thread even during heavy computation.
    
    Args:
        training_data_json: JSON string of training data
        config_dict: Configuration dictionary
        result_queue: Queue to send results back
    """
    try:
        # Import here to avoid issues with multiprocessing on Windows
        import json
        import numpy as np
        import pickle
        import tempfile
        from datetime import datetime
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.svm import SVC
        from sklearn.neural_network import MLPClassifier
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
        from models.ml_models import MLTrainingData, MLConfig
        
        # Parse training data
        data_list = json.loads(training_data_json)
        training_data = []
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
            training_data.append(sample)
        
        # Create config
        config = MLConfig(**config_dict)
        
        # Prepare data
        X = np.array([sample.to_features() for sample in training_data])
        y = np.array([sample.event for sample in training_data])
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=config.test_size,
            random_state=config.random_state,
            stratify=y
        )
        
        # Create model
        if config.model_type == 'random_forest':
            model = RandomForestClassifier(
                n_estimators=config.n_estimators,
                max_depth=config.max_depth,
                random_state=config.random_state
            )
        elif config.model_type == 'svm':
            model = SVC(
                kernel='rbf',
                probability=True,
                random_state=config.random_state
            )
        elif config.model_type == 'neural_network':
            model = MLPClassifier(
                hidden_layer_sizes=(100, 50),
                max_iter=500,
                random_state=config.random_state
            )
        else:
            raise ValueError(f"Unknown model type: {config.model_type}")
        
        # Train (this is the heavy computation that would block UI)
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)
        
        train_accuracy = accuracy_score(y_train, y_pred_train)
        test_accuracy = accuracy_score(y_test, y_pred_test)
        
        # Save model to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pkl')
        temp_path = temp_file.name
        temp_file.close()
        
        with open(temp_path, 'wb') as f:
            pickle.dump(model, f)
        
        # Return metrics
        metrics = {
            'train_accuracy': train_accuracy,
            'test_accuracy': test_accuracy,
            'n_samples': len(training_data),
            'n_features': X.shape[1],
            'model_type': config.model_type,
            'classification_report': classification_report(y_test, y_pred_test),
            'confusion_matrix': confusion_matrix(y_test, y_pred_test).tolist(),
            'model_path': temp_path  # Path to saved model
        }
        
        result_queue.put(('success', metrics))
        
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        result_queue.put(('error', error_msg))


class MLTrainerService(QObject):
    """Service for training ML models on EEG data"""
    
    # Signals
    auto_training_started = pyqtSignal()
    auto_training_completed = pyqtSignal(dict)  # metrics
    auto_training_failed = pyqtSignal(str)  # error message
    model_updated = pyqtSignal()  # Model was retrained
    
    def __init__(self, config: Optional[MLConfig] = None, parent=None):
        """
        Initialize ML trainer service
        
        Args:
            config: ML configuration
            parent: Parent QObject
        """
        super().__init__(parent)
        self.config = config or MLConfig()
        self.model = None
        self.training_data: List[MLTrainingData] = []
        self.is_trained = False
        
        # Last training metrics (for display)
        self.last_training_metrics: Optional[Dict] = None
        
        # Process management (using multiprocessing instead of threading)
        self._training_process: Optional[Process] = None
        self._result_queue: Optional[Queue] = None
        self._training_lock = Lock()
        self._is_training = False
        
        # Timer for checking process results
        self._result_timer = QTimer()
        self._result_timer.timeout.connect(self._check_process_result)
        self._result_timer.setInterval(100)  # Check every 100ms
        
        # Auto-training settings
        self.auto_train_enabled = getattr(self.config, 'auto_train_enabled', True)
        self.auto_train_min_new_samples = getattr(self.config, 'auto_train_min_new_samples', 5)
        self._samples_since_last_train = 0
        
        # Load existing training data if available
        self._load_training_data()
        
        logger.info("MLTrainerService initialized")
    
    def add_training_sample(self, data: MLTrainingData):
        """
        Add a training sample and optionally trigger auto-training
        
        Args:
            data: Training data sample
        """
        with self._training_lock:
            self.training_data.append(data)
            self._samples_since_last_train += 1
        
        logger.debug(f"Added training sample: event={data.event}, features={len(data.to_features())}")
        
        # Auto-save training data (outside lock to avoid blocking)
        self.save_training_data()
        
        # Check if we should auto-train (outside lock)
        if self.auto_train_enabled:
            self._check_and_auto_train()
    
    def _check_and_auto_train(self):
        """
        Check if we have enough new samples and can train, then start auto-training
        """
        # Don't start new training if one is already running
        if self._is_training:
            logger.debug("Training already in progress, skipping auto-train check")
            return
        
        # Check if we have enough new samples since last training
        if self._samples_since_last_train < self.auto_train_min_new_samples:
            logger.debug(f"Not enough new samples for auto-train: {self._samples_since_last_train} < {self.auto_train_min_new_samples}")
            return
        
        # Check if we can train (enough samples per class)
        can_train, reason = self.can_train()
        if not can_train:
            logger.debug(f"Cannot auto-train yet: {reason}")
            return
        
        # Start training in background
        logger.info(f"Starting auto-training (new samples: {self._samples_since_last_train})")
        self.start_auto_training()
    
    def start_auto_training(self):
        """
        Start model training in separate process (to avoid blocking UI)
        """
        if self._is_training:
            logger.warning("Training already in progress")
            return
        
        # Check if can train
        can_train, reason = self.can_train()
        if not can_train:
            logger.warning(f"Cannot start training: {reason}")
            self.auto_training_failed.emit(reason)
            return
        
        # Prepare training data for process
        with self._training_lock:
            training_data_copy = list(self.training_data)
        
        # Convert training data to JSON
        data_list = []
        for sample in training_data_copy:
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
        
        training_data_json = json.dumps(data_list)
        
        # Convert config to dict
        config_dict = {
            'model_type': self.config.model_type,
            'n_estimators': self.config.n_estimators,
            'max_depth': self.config.max_depth,
            'random_state': self.config.random_state,
            'test_size': self.config.test_size,
            'min_samples_per_class': self.config.min_samples_per_class,
            'auto_train_enabled': self.config.auto_train_enabled,
            'auto_train_min_new_samples': self.config.auto_train_min_new_samples,
            'confidence_threshold': self.config.confidence_threshold,
            'model_path': self.config.model_path,
            'training_data_path': self.config.training_data_path
        }
        
        # Create result queue
        self._result_queue = Queue()
        
        # Create and start training process
        self._is_training = True
        self._training_process = Process(
            target=_train_model_in_process,
            args=(training_data_json, config_dict, self._result_queue)
        )
        self._training_process.start()
        
        # Start timer to check for results
        self._result_timer.start()
        
        # Emit started signal
        self._on_training_started()
        
        logger.info("Training process started (PID: {})".format(self._training_process.pid))
    
    def _on_training_started(self):
        """Handle training started signal"""
        logger.info("Background training started")
        self.auto_training_started.emit()
    
    def _on_training_completed(self, metrics: dict):
        """Handle training completed signal"""
        logger.info(f"Background training completed: accuracy={metrics.get('test_accuracy', 0):.3f}")
        self._samples_since_last_train = 0  # Reset counter
        self.auto_training_completed.emit(metrics)
        self.model_updated.emit()
    
    def _on_training_failed(self, error_msg: str):
        """Handle training failed signal"""
        logger.error(f"Background training failed: {error_msg}")
        self.auto_training_failed.emit(error_msg)
    
    def _check_process_result(self):
        """Check for results from training process"""
        if not self._is_training:
            self._result_timer.stop()
            return
        
        if not self._result_queue:
            self._result_timer.stop()
            return
        
        try:
            # Check if process is still alive
            if self._training_process and not self._training_process.is_alive():
                # Process finished but no result in queue - might be an error
                if self._result_queue.empty():
                    logger.warning("Training process finished but no result in queue")
                    self._on_training_failed("Training process terminated unexpectedly")
                    self._cleanup_process()
                    return
            
            # Check if result is available (non-blocking)
            if not self._result_queue.empty():
                result_type, result_data = self._result_queue.get()
                
                # Stop timer
                self._result_timer.stop()
                
                if result_type == 'success':
                    # Load model from temporary file
                    temp_model_path = result_data.pop('model_path', None)
                    if not temp_model_path or not os.path.exists(temp_model_path):
                        logger.error("Model file not found from training process")
                        self._on_training_failed("Model file not found")
                        self._cleanup_process()
                        return
                    
                    try:
                        with open(temp_model_path, 'rb') as f:
                            self.model = pickle.load(f)
                        
                        # Move to final location
                        final_path = Path(self.config.model_path)
                        final_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        with open(final_path, 'wb') as f:
                            pickle.dump(self.model, f)
                        
                        # Delete temp file
                        try:
                            os.unlink(temp_model_path)
                        except:
                            pass  # Ignore errors deleting temp file
                        
                        # Update state
                        with self._training_lock:
                            self.is_trained = True
                            self.last_training_metrics = result_data.copy()
                        
                        logger.info("Model loaded from training process")
                        self._on_training_completed(result_data)
                        
                    except Exception as e:
                        logger.error(f"Error loading model from process: {e}", exc_info=True)
                        self._on_training_failed(f"Failed to load trained model: {e}")
                    
                elif result_type == 'error':
                    self._on_training_failed(result_data)
                
                # Cleanup
                self._cleanup_process()
        
        except Exception as e:
            logger.error(f"Error checking process result: {e}", exc_info=True)
            self._cleanup_process()
    
    def _cleanup_process(self):
        """Cleanup training process"""
        self._is_training = False
        
        # Stop result timer
        if hasattr(self, '_result_timer'):
            self._result_timer.stop()
        
        if self._training_process:
            try:
                if self._training_process.is_alive():
                    logger.info(f"Terminating training process (PID: {self._training_process.pid})")
                    self._training_process.terminate()
                    self._training_process.join(timeout=2.0)
                    if self._training_process.is_alive():
                        logger.warning("Force killing training process")
                        self._training_process.kill()
                        self._training_process.join(timeout=1.0)
                    else:
                        logger.info("Training process terminated successfully")
            except Exception as e:
                logger.warning(f"Error cleaning up process: {e}")
            finally:
                self._training_process = None
        
        self._result_queue = None
    
    def cleanup(self):
        """
        Cleanup all resources (called on application shutdown)
        """
        logger.info("Cleaning up ML trainer service")
        
        # Stop any running training
        if self._is_training:
            self._cleanup_process()
        
        # Stop result timer
        if hasattr(self, '_result_timer'):
            self._result_timer.stop()
        
        # Close result queue if exists
        if self._result_queue:
            try:
                # Try to get any remaining items to prevent hanging
                while not self._result_queue.empty():
                    try:
                        self._result_queue.get_nowait()
                    except:
                        break
            except:
                pass
            self._result_queue = None
        
        logger.info("ML trainer service cleaned up")
    
    def _on_training_process_finished(self):
        """Handle training process finished"""
        self._is_training = False
        if self._training_process:
            self._training_process.join(timeout=1.0)
            self._training_process = None
    
    def set_auto_train_enabled(self, enabled: bool):
        """
        Enable or disable auto-training
        
        Args:
            enabled: True to enable auto-training
        """
        self.auto_train_enabled = enabled
        logger.info(f"Auto-training {'enabled' if enabled else 'disabled'}")
    
    def is_training(self) -> bool:
        """Check if training is currently in progress"""
        return self._is_training
    
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
        with self._training_lock:
            training_data_copy = list(self.training_data)
        
        stats = {}
        for event_type in EventType:
            count = sum(1 for sample in training_data_copy if sample.event == event_type.value)
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
        
        Requires minimum number of classes (default: 2) with enough samples each.
        This allows training with just 2 events (e.g., ml and mr) instead of all 5.
        
        Returns:
            (can_train, reason)
        """
        with self._training_lock:
            if len(self.training_data) == 0:
                return False, "No training data available"
        
        stats = self.get_training_stats()
        min_samples = self.config.min_samples_per_class
        min_classes = getattr(self.config, 'min_classes_required', 2)
        
        # Count classes with enough samples
        valid_classes = []
        invalid_classes = []
        
        for event, count in stats.items():
            if count >= min_samples:
                valid_classes.append((event, count))
            else:
                invalid_classes.append((event, count))
        
        # Check if we have enough valid classes
        if len(valid_classes) < min_classes:
            if invalid_classes:
                missing = ", ".join([f"'{event}' ({count} < {min_samples})" for event, count in invalid_classes])
                return False, f"Need at least {min_classes} classes with {min_samples}+ samples. Missing: {missing}"
            else:
                return False, f"Need at least {min_classes} classes with {min_samples}+ samples. Found: {len(valid_classes)}"
        
        # All good!
        class_names = ", ".join([event for event, _ in valid_classes])
        return True, f"Ready to train with {len(valid_classes)} classes: {class_names}"
    
    def train_model(self, use_process: bool = True) -> Optional[Dict[str, any]]:
        """
        Train ML model on collected data
        
        Args:
            use_process: If True, train in separate process (non-blocking).
                        If False, train in current process (blocking, for compatibility)
        
        Returns:
            Training metrics and results (None if use_process=True, as it's async)
        """
        if use_process:
            # Use process-based training (non-blocking)
            self.start_auto_training()
            return None  # Async - results will come via signals
        
        # Synchronous training (for backward compatibility, but may block)
        logger.warning("Using synchronous training - this may block UI!")
        logger.info("Starting model training...")
        
        # Use lock to ensure thread-safety
        with self._training_lock:
            # Check if can train
            can_train, reason = self.can_train()
            if not can_train:
                logger.error(f"Cannot train model: {reason}")
                raise ValueError(reason)
            
            # Prepare data (create copy to avoid race conditions)
            training_data_copy = list(self.training_data)
        
        # Prepare data outside lock (numpy operations can be slow)
        X = np.array([sample.to_features() for sample in training_data_copy])
        y = np.array([sample.event for sample in training_data_copy])
        
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
        
        # Save model and training data (with lock)
        with self._training_lock:
            self.save_model()
            self.is_trained = True
        
        # Return metrics
        metrics = {
            'train_accuracy': train_accuracy,
            'test_accuracy': test_accuracy,
            'n_samples': len(training_data_copy),  # Use copy to avoid lock issues
            'n_features': X.shape[1],
            'model_type': self.config.model_type,
            'classification_report': classification_report(y_test, y_pred_test),
            'confusion_matrix': confusion_matrix(y_test, y_pred_test).tolist()
        }
        
        # Save last training metrics
        with self._training_lock:
            self.last_training_metrics = metrics.copy()
        
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
            True if model loaded successfully and validated
        """
        try:
            path = Path(self.config.model_path)
            if not path.exists():
                logger.info("No saved model found")
                return False
            
            with open(path, 'rb') as f:
                self.model = pickle.load(f)
            
            # Validate loaded model
            if self.model is None:
                logger.error("Loaded model is None")
                self.is_trained = False
                return False
            
            # Check if model has required methods
            if not hasattr(self.model, 'predict'):
                logger.error("Loaded model does not have predict method")
                self.model = None
                self.is_trained = False
                return False
            
            # Test model with dummy data to ensure it works
            try:
                import numpy as np
                # Create dummy features (10 features matching MLTrainingData)
                dummy_features = [50.0] * 10  # All features = 50
                X_test = np.array([dummy_features])
                _ = self.model.predict(X_test)
                logger.debug("Model validation test passed")
            except Exception as e:
                logger.error(f"Model validation test failed: {e}", exc_info=True)
                self.model = None
                self.is_trained = False
                return False
            
            self.is_trained = True
            logger.info(f"Model loaded and validated from {path}")
            return True
        
        except Exception as e:
            logger.error(f"Error loading model: {e}", exc_info=True)
            self.model = None
            self.is_trained = False
            return False
    
    def clear_training_data(self):
        """Clear all training data"""
        self.training_data.clear()
        logger.info("Training data cleared")
