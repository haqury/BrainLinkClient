"""ML Control Form for training and managing ML models"""

import logging
import pickle
import numpy as np
from pathlib import Path
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QTextEdit, QCheckBox, QMessageBox, QProgressBar, QFileDialog, QSlider
)
from PyQt5.QtCore import Qt, QTimer

from services.ml_trainer_service import MLTrainerService
from services.ml_predictor_service import MLPredictorService
from models.event_types import EventType

logger = logging.getLogger(__name__)


class MLControlForm(QDialog):
    """Separate window for ML model training and control"""
    
    def __init__(self, ml_trainer: MLTrainerService, ml_predictor: MLPredictorService, parent=None):
        """
        Initialize ML control form
        
        Args:
            ml_trainer: ML trainer service
            ml_predictor: ML predictor service
            parent: Parent window
        """
        super().__init__(parent)
        self.ml_trainer = ml_trainer
        self.ml_predictor = ml_predictor
        self.parent_window = parent
        
        # Make it a proper separate window
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        self.setModal(False)
        
        # Timer for auto-updating statistics
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.setInterval(1000)  # Update every second
        
        self.init_ui()
        self.update_status()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("ML Model Control - BrainLink")
        self.resize(600, 700)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # ==================== Status Section ====================
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        
        self.lbl_model_status = QLabel("Model: Not trained")
        self.lbl_model_status.setStyleSheet("font-size: 11pt;")
        status_layout.addWidget(self.lbl_model_status)
        
        self.lbl_training_data = QLabel("Training samples: 0")
        self.lbl_training_data.setStyleSheet("font-size: 11pt;")
        status_layout.addWidget(self.lbl_training_data)
        
        self.lbl_model_trained_on = QLabel("Model trained on: -")
        self.lbl_model_trained_on.setStyleSheet("font-size: 10pt; color: #888;")
        status_layout.addWidget(self.lbl_model_trained_on)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # ==================== Data Collection Section ====================
        collection_group = QGroupBox("Step 1: Collect Training Data")
        collection_layout = QVBoxLayout()
        
        self.chk_collect = QCheckBox("Enable Data Collection")
        self.chk_collect.setStyleSheet("font-size: 11pt; font-weight: bold;")
        self.chk_collect.stateChanged.connect(self.on_collect_changed)
        collection_layout.addWidget(self.chk_collect)
        
        # Restore persisted state from parent window (so it survives close/open)
        if self.parent_window and hasattr(self.parent_window, "_is_collecting_training_data"):
            self.chk_collect.setChecked(bool(self.parent_window._is_collecting_training_data))
        
        info_label = QLabel(
            "Enable this to collect EEG data with events.\n"
            "Select events in main window using checkboxes."
        )
        info_label.setWordWrap(True)
        collection_layout.addWidget(info_label)
        
        # Buttons row 1 (only statistics are relevant now)
        btn_row1 = QHBoxLayout()
        self.btn_show_stats = QPushButton("Show Statistics")
        self.btn_show_stats.clicked.connect(self.on_show_stats)
        btn_row1.addWidget(self.btn_show_stats)
        btn_row1.addStretch()
        collection_layout.addLayout(btn_row1)
        
        # Buttons row 2 (only 'Clear All Data' is still useful)
        btn_row2 = QHBoxLayout()
        self.btn_clear_data = QPushButton("Clear All Data")
        self.btn_clear_data.clicked.connect(self.on_clear_data)
        btn_row2.addWidget(self.btn_clear_data)
        btn_row2.addStretch()
        collection_layout.addLayout(btn_row2)
        
        collection_group.setLayout(collection_layout)
        layout.addWidget(collection_group)
        
        # ==================== Training Section ====================
        training_group = QGroupBox("Step 2: Train Model")
        training_layout = QVBoxLayout()
        
        self.btn_train = QPushButton("TRAIN MODEL")
        self.btn_train.clicked.connect(self.on_train_clicked)
        self.btn_train.setMinimumHeight(45)
        self.btn_train.setStyleSheet("font-size: 12pt; font-weight: bold;")
        training_layout.addWidget(self.btn_train)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        training_layout.addWidget(self.progress_bar)
        
        # Model save/load buttons
        model_buttons = QHBoxLayout()
        self.btn_save_model = QPushButton("💾 Save Model")
        self.btn_save_model.clicked.connect(self.on_save_model_clicked)
        self.btn_save_model.setToolTip("Save trained model to file")
        model_buttons.addWidget(self.btn_save_model)
        
        self.btn_load_model = QPushButton("📂 Load Model")
        self.btn_load_model.clicked.connect(self.on_load_model_clicked)
        self.btn_load_model.setToolTip("Load model from file")
        model_buttons.addWidget(self.btn_load_model)
        
        training_layout.addLayout(model_buttons)
        
        training_group.setLayout(training_layout)
        layout.addWidget(training_group)
        
        # ==================== Prediction Control Section ====================
        prediction_group = QGroupBox("Step 3: Use ML Prediction")
        prediction_layout = QVBoxLayout()
        
        self.chk_use_ml = QCheckBox("Enable ML Prediction")
        self.chk_use_ml.setStyleSheet("font-size: 11pt; font-weight: bold;")
        self.chk_use_ml.setToolTip("Use ML model instead of rule-based detection")
        self.chk_use_ml.stateChanged.connect(self.on_use_ml_changed)
        prediction_layout.addWidget(self.chk_use_ml)
        
        self.chk_invert_ml_mr = QCheckBox("Invert ML/MR (fix if ml works as right)")
        self.chk_invert_ml_mr.setStyleSheet("font-size: 10pt;")
        self.chk_invert_ml_mr.setToolTip("If ML predicts 'ml' but it moves right, enable this to swap ml/mr")
        self.chk_invert_ml_mr.setChecked(self.ml_trainer.config.invert_ml_mr)
        self.chk_invert_ml_mr.stateChanged.connect(self.on_invert_ml_mr_changed)
        prediction_layout.addWidget(self.chk_invert_ml_mr)

        # Confidence threshold slider
        confidence_row = QHBoxLayout()
        confidence_row.addWidget(QLabel("Confidence threshold:"))
        
        self.confidence_slider = QSlider(Qt.Horizontal)
        self.confidence_slider.setRange(0, 100)  # 0.00 to 1.00
        self.confidence_slider.setSingleStep(1)
        self.confidence_slider.setPageStep(5)
        
        initial_threshold = self.ml_trainer.config.confidence_threshold
        initial_threshold = max(0.0, min(1.0, float(initial_threshold)))
        self.confidence_slider.setValue(int(round(initial_threshold * 100)))
        
        self.confidence_label = QLabel(f"{initial_threshold:.2f}")
        self.confidence_label.setMinimumWidth(40)
        self.confidence_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        def on_confidence_change(v: int):
            threshold = float(v) / 100.0
            self.ml_trainer.config.confidence_threshold = threshold
            self.ml_predictor.config.confidence_threshold = threshold
            self.confidence_label.setText(f"{threshold:.2f}")
            logger.info(f"Confidence threshold updated: {threshold:.2f}")
        
        self.confidence_slider.valueChanged.connect(on_confidence_change)
        
        confidence_row.addWidget(self.confidence_slider, stretch=1)
        confidence_row.addWidget(self.confidence_label)
        
        confidence_info = QLabel("Minimum confidence for ML prediction (lower = more predictions, higher = more confident only)")
        confidence_info.setStyleSheet("font-size: 9pt; color: #888;")
        confidence_info.setWordWrap(True)
        
        prediction_layout.addLayout(confidence_row)
        prediction_layout.addWidget(confidence_info)

        # Feature weights (simple sliders)
        weights_group = QGroupBox("Feature weights (lower = less influence)")
        weights_layout = QVBoxLayout()

        self._weight_value_labels = {}
        self._weight_sliders = {}

        # Only expose the two most sensitive parameters by default
        self._add_weight_slider(weights_layout, "attention", "Attention")
        self._add_weight_slider(weights_layout, "meditation", "Meditation")

        note = QLabel("Note: changing weights affects prediction immediately, but retrain is recommended.")
        note.setStyleSheet("font-size: 9pt; color: #888;")
        note.setWordWrap(True)
        weights_layout.addWidget(note)

        weights_group.setLayout(weights_layout)
        prediction_layout.addWidget(weights_group)
        
        prediction_group.setLayout(prediction_layout)
        layout.addWidget(prediction_group)
        
        # ==================== Results Section ====================
        results_group = QGroupBox("Training Results")
        results_layout = QVBoxLayout()
        
        self.txt_results = QTextEdit()
        self.txt_results.setReadOnly(True)
        self.txt_results.setPlaceholderText("Training results will appear here...")
        results_layout.addWidget(self.txt_results)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        self.setLayout(layout)
        
        # Start auto-update timer when window is shown
        self.update_timer.start()
        
        logger.info("ML Control Form initialized")
    
    def update_status(self):
        """Update status labels"""
        # Keep "Enable Data Collection" synced with main window state
        if self.parent_window and hasattr(self.parent_window, "_is_collecting_training_data"):
            desired = bool(self.parent_window._is_collecting_training_data)
            if self.chk_collect.isChecked() != desired:
                self.chk_collect.blockSignals(True)
                self.chk_collect.setChecked(desired)
                self.chk_collect.blockSignals(False)

        if self.ml_predictor.is_ready():
            self.lbl_model_status.setText("Model: ✓ Trained and ready")
            self.lbl_model_status.setStyleSheet("color: green; font-size: 11pt; font-weight: bold;")
            self.chk_use_ml.setEnabled(True)
            self.btn_save_model.setEnabled(True)
            if hasattr(self.parent_window, 'chk_use_ml_prediction'):
                self.chk_use_ml.setChecked(self.parent_window.chk_use_ml_prediction.isChecked())
        else:
            self.lbl_model_status.setText("Model: ✗ Not trained")
            self.lbl_model_status.setStyleSheet("color: red; font-size: 11pt;")
            self.chk_use_ml.setEnabled(True)  # Keep enabled; do not uncheck when no model
            self.btn_save_model.setEnabled(False)
            if hasattr(self.parent_window, 'chk_use_ml_prediction'):
                self.chk_use_ml.setChecked(self.parent_window.chk_use_ml_prediction.isChecked())
        
        # Show data stored in the trained model (if model is trained)
        if self.ml_trainer.is_trained and self.ml_trainer.model:
            # Model is trained - show data from the model
            if hasattr(self.ml_trainer, 'last_training_metrics') and self.ml_trainer.last_training_metrics:
                # We have metrics with training data info
                metrics = self.ml_trainer.last_training_metrics
                n_samples = metrics.get('n_samples', 0)
                
                # Get event distribution from metrics (if available)
                event_distribution = metrics.get('event_distribution', {})
                
                if event_distribution:
                    # Build full distribution over all known events (including zero-count)
                    full_distribution = {
                        event_type.value: event_distribution.get(event_type.value, 0)
                        for event_type in EventType
                    }
                    details = ", ".join(
                        [f"{event}: {count}" for event, count in sorted(full_distribution.items())]
                    )
                    self.lbl_training_data.setText(f"Model data: {n_samples} samples ({details})")
                else:
                    # Fallback to model classes if no distribution
                    if hasattr(self.ml_trainer.model, 'classes_'):
                        model_classes = list(self.ml_trainer.model.classes_)
                        classes_str = ", ".join(sorted(model_classes))
                        self.lbl_training_data.setText(
                            f"Model data: {n_samples} samples (classes: {classes_str})"
                        )
                    else:
                        self.lbl_training_data.setText(f"Model data: {n_samples} samples")
            else:
                # Model loaded but no metrics - show classes from model
                if hasattr(self.ml_trainer.model, 'classes_'):
                    model_classes = list(self.ml_trainer.model.classes_)
                    classes_str = ", ".join(sorted(model_classes))
                    self.lbl_training_data.setText(f"Model data: classes ({classes_str})")
                else:
                    self.lbl_training_data.setText("Model data: loaded (no details)")
        else:
            # Model not trained - show current training data
            stats = self.ml_trainer.get_training_stats()
            total = sum(stats.values())
            
            if stats:
                details = ", ".join([f"{event}: {count}" for event, count in sorted(stats.items())])
                self.lbl_training_data.setText(f"Training samples: {total} ({details})")
            else:
                self.lbl_training_data.setText(f"Training samples: {total}")
        
        self.lbl_training_data.setStyleSheet("font-size: 11pt;")
        
        # Show last training metrics if available
        if hasattr(self.ml_trainer, 'last_training_metrics') and self.ml_trainer.last_training_metrics:
            metrics = self.ml_trainer.last_training_metrics
            n_samples = metrics.get('n_samples', 0)
            test_accuracy = metrics.get('test_accuracy', 0)
            self.lbl_model_trained_on.setText(
                f"Model trained on: {n_samples} samples (accuracy: {test_accuracy:.1%})"
            )
            self.lbl_model_trained_on.setStyleSheet("font-size: 10pt; color: #4CAF50;")
        else:
            self.lbl_model_trained_on.setText("Model trained on: -")
            self.lbl_model_trained_on.setStyleSheet("font-size: 10pt; color: #888;")
    
    def on_collect_changed(self, state):
        """Handle collect training data checkbox"""
        if self.parent_window:
            self.parent_window._is_collecting_training_data = (state == Qt.Checked)
            logger.info(f"Training data collection: {'enabled' if state == Qt.Checked else 'disabled'}")
    
    def on_show_stats(self):
        """Show training data statistics"""
        stats = self.ml_trainer.get_training_stats()
        
        msg = "Training Data Statistics:\n\n"
        for event, count in stats.items():
            msg += f"  {event}: {count} samples\n"
        
        msg += f"\nTotal: {sum(stats.values())} samples"
        
        QMessageBox.information(self, "Training Data Statistics", msg)
    
    def on_save_data(self):
        """Deprecated: previously saved training data to file (no longer used)."""
        QMessageBox.information(self, "Info", "Saving ML training data is no longer needed.\nData for the model comes directly from history and live collection.")
    
    def on_clear_data(self):
        """Clear all training data"""
        reply = QMessageBox.question(
            self,
            "Confirm Clear",
            "Are you sure you want to clear all training data?\n\n"
            "This only clears the ML training dataset in memory.\n"
            "History (raw records) will remain unchanged.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.ml_trainer.clear_training_data()
            self.update_status()
            logger.info("Training data cleared")
    
    def on_train_clicked(self):
        """Train the ML model or reset it if there is no data"""
        # Special case: no training data at all -> offer to reset (clear) model
        stats = self.ml_trainer.get_training_stats()
        total_samples = sum(stats.values())
        if total_samples == 0:
            reply = QMessageBox.question(
                self,
                "Reset Model",
                "There is no training data (history is effectively empty).\n\n"
                "Do you want to reset (clear) the current ML model,\n"
                "so you can start collecting a fresh dataset?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self.ml_trainer.reset_model()
                self.update_status()
                QMessageBox.information(
                    self,
                    "Model Reset",
                    "ML model has been reset.\n\n"
                    "You can now start collecting new data and retrain."
                )
            return

        # Normal path: there is data, check if we can train
        can_train, reason = self.ml_trainer.can_train()
        if not can_train:
            QMessageBox.warning(
                self,
                "Cannot Train",
                f"Cannot train model:\n{reason}\n\n"
                f"Please collect more balanced training data first."
            )
            return
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.btn_train.setEnabled(False)
        
        # Connect to training signals for manual training
        if not hasattr(self, '_training_connected'):
            self.ml_trainer.auto_training_completed.connect(self._on_manual_training_completed)
            self.ml_trainer.auto_training_failed.connect(self._on_manual_training_failed)
            self._training_connected = True
        
        # Start training in process (non-blocking)
        try:
            logger.info("Starting model training in separate process...")
            # This will start process and return None (async)
            self.ml_trainer.train_model(use_process=True)
            # Results will come via signals
        except Exception as e:
            logger.error(f"Error starting training: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Training Failed",
                f"Failed to start training:\n{e}"
            )
            self.progress_bar.setVisible(False)
            self.btn_train.setEnabled(True)
    
    def _on_manual_training_completed(self, metrics: dict):
        """Handle manual training completion"""
        # Check if this is from manual training (progress bar visible)
        if not self.progress_bar.isVisible():
            return  # This is from auto-training, ignore
        
        try:
            # Show results
            results_text = f"Training completed successfully!\n\n"
            results_text += f"Training accuracy: {metrics['train_accuracy']:.3f}\n"
            results_text += f"Testing accuracy: {metrics['test_accuracy']:.3f}\n"
            results_text += f"Samples: {metrics['n_samples']}\n"
            results_text += f"Model type: {metrics['model_type']}\n\n"
            results_text += "Classification Report:\n"
            results_text += metrics['classification_report']
            
            self.txt_results.setText(results_text)
            
            # Update status
            self.update_status()
            
            QMessageBox.information(
                self,
                "Training Complete",
                f"Model trained successfully!\n\n"
                f"Test accuracy: {metrics['test_accuracy']:.1%}"
            )
        finally:
            self.progress_bar.setVisible(False)
            self.btn_train.setEnabled(True)
    
    def _on_manual_training_failed(self, error_msg: str):
        """Handle manual training failure"""
        # Check if this is from manual training (progress bar visible)
        if not self.progress_bar.isVisible():
            return  # This is from auto-training, ignore
        
        QMessageBox.critical(
            self,
            "Training Failed",
            f"Failed to train model:\n{error_msg}"
        )
        
        self.progress_bar.setVisible(False)
        self.btn_train.setEnabled(True)
    
    def on_use_ml_changed(self, state):
        """Handle use ML prediction checkbox (never auto-uncheck; no errors if model missing)."""
        if self.parent_window:
            enabled = (state == Qt.Checked)
            self.parent_window._use_ml_prediction = enabled
            logger.info(f"ML prediction: {'enabled' if enabled else 'disabled'}")
            if hasattr(self.parent_window, 'chk_use_ml_prediction'):
                self.parent_window.chk_use_ml_prediction.blockSignals(True)
                self.parent_window.chk_use_ml_prediction.setChecked(enabled)
                self.parent_window.chk_use_ml_prediction.blockSignals(False)
    
    def on_invert_ml_mr_changed(self, state):
        """Handle invert ml/mr checkbox"""
        enabled = (state == Qt.Checked)
        self.ml_trainer.config.invert_ml_mr = enabled
        self.ml_predictor.config.invert_ml_mr = enabled
        logger.info(f"ML/MR inversion: {'enabled' if enabled else 'disabled'}")
    
    def showEvent(self, event):
        """Handle window show event - start auto-update timer"""
        super().showEvent(event)
        self.update_timer.start()
        self.update_status()  # Update immediately when shown
    
    def hideEvent(self, event):
        """Handle window hide event - stop auto-update timer"""
        super().hideEvent(event)
        self.update_timer.stop()
    
    def refresh_stats(self):
        """Refresh statistics display (called after training)"""
        self.update_status()

    def _add_weight_slider(self, parent_layout: QVBoxLayout, feature_key: str, title: str):
        """Add a weight slider row (0..100 -> 0.00..1.00)."""
        row = QHBoxLayout()
        row.addWidget(QLabel(f"{title}:"))

        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 100)
        slider.setSingleStep(1)
        slider.setPageStep(5)

        weights = getattr(self.ml_trainer.config, "feature_weights", {}) or {}
        initial = float(weights.get(feature_key, 1.0))
        initial = max(0.0, min(1.0, initial))
        slider.setValue(int(round(initial * 100)))

        value_lbl = QLabel(f"{initial:.2f}")
        value_lbl.setMinimumWidth(40)
        value_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        def on_change(v: int):
            w = float(v) / 100.0
            self._set_feature_weight(feature_key, w)
            value_lbl.setText(f"{w:.2f}")

        slider.valueChanged.connect(on_change)

        self._weight_sliders[feature_key] = slider
        self._weight_value_labels[feature_key] = value_lbl

        row.addWidget(slider, stretch=1)
        row.addWidget(value_lbl)
        parent_layout.addLayout(row)

    def _set_feature_weight(self, feature_key: str, weight: float):
        """Update feature weight in both trainer and predictor configs."""
        weight = max(0.0, min(1.0, float(weight)))

        for cfg in (self.ml_trainer.config, self.ml_predictor.config):
            weights = getattr(cfg, "feature_weights", None)
            if weights is None:
                cfg.feature_weights = {}
                weights = cfg.feature_weights
            weights[feature_key] = weight

        logger.info(f"Feature weight updated: {feature_key}={weight:.2f}")
    
    def on_save_model_clicked(self):
        """Save trained model to file"""
        if not self.ml_trainer.is_trained or self.ml_trainer.model is None:
            QMessageBox.warning(
                self,
                "No Model",
                "No trained model to save.\n\n"
                "Please train a model first."
            )
            return
        
        # Get save path from user
        default_path = self.ml_trainer.config.model_path
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save ML Model",
            default_path,
            "Pickle Files (*.pkl);;All Files (*)"
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            # Save model to selected path
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'wb') as f:
                pickle.dump(self.ml_trainer.model, f)
            
            # Also update config path if user wants
            reply = QMessageBox.question(
                self,
                "Save Successful",
                f"Model saved successfully to:\n{file_path}\n\n"
                f"Use this as default model path?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.ml_trainer.config.model_path = file_path
                logger.info(f"Updated default model path to: {file_path}")
            
            logger.info(f"Model saved to {file_path}")
            
        except Exception as e:
            logger.error(f"Error saving model: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Save Failed",
                f"Failed to save model:\n{e}"
            )
    
    def on_load_model_clicked(self):
        """Load trained model from file"""
        # Get load path from user
        default_path = self.ml_trainer.config.model_path
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load ML Model",
            str(Path(default_path).parent) if default_path else "",
            "Pickle Files (*.pkl);;All Files (*)"
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            # Load model from selected path
            path = Path(file_path)
            if not path.exists():
                QMessageBox.warning(
                    self,
                    "File Not Found",
                    f"File not found:\n{file_path}"
                )
                return
            
            with open(path, 'rb') as f:
                model = pickle.load(f)
            
            # Validate loaded model
            if model is None:
                raise ValueError("Loaded model is None")
            
            if not hasattr(model, 'predict'):
                raise ValueError("Loaded model does not have predict method")
            
            # Test model with dummy data
            dummy_features = [50.0] * 10
            X_test = np.array([dummy_features])
            _ = model.predict(X_test)
            
            # Set model
            self.ml_trainer.model = model
            self.ml_trainer.is_trained = True
            
            # Update config path if user wants
            reply = QMessageBox.question(
                self,
                "Load Successful",
                f"Model loaded successfully from:\n{file_path}\n\n"
                f"Model validated and ready to use.\n\n"
                f"Use this as default model path?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.No:
                # Still update path for convenience
                self.ml_trainer.config.model_path = file_path
            else:
                self.ml_trainer.config.model_path = file_path
            
            # Reload predictor to use new model
            self.ml_predictor.trainer = self.ml_trainer
            
            # Update UI
            self.update_status()
            
            logger.info(f"Model loaded from {file_path}")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Load Failed",
                f"Failed to load model:\n{e}\n\n"
                f"Make sure the file is a valid trained model."
            )
