"""ML Control Form for training and managing ML models"""

import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QTextEdit, QCheckBox, QMessageBox, QProgressBar
)
from PyQt5.QtCore import Qt

from services.ml_trainer_service import MLTrainerService
from services.ml_predictor_service import MLPredictorService

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
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # ==================== Data Collection Section ====================
        collection_group = QGroupBox("Step 1: Collect Training Data")
        collection_layout = QVBoxLayout()
        
        self.chk_collect = QCheckBox("Enable Data Collection")
        self.chk_collect.setStyleSheet("font-size: 11pt; font-weight: bold;")
        self.chk_collect.stateChanged.connect(self.on_collect_changed)
        collection_layout.addWidget(self.chk_collect)
        
        info_label = QLabel(
            "Enable this to collect EEG data with events.\n"
            "Select events in main window using checkboxes."
        )
        info_label.setWordWrap(True)
        collection_layout.addWidget(info_label)
        
        # Buttons row 1
        btn_row1 = QHBoxLayout()
        self.btn_show_stats = QPushButton("Show Statistics")
        self.btn_show_stats.clicked.connect(self.on_show_stats)
        btn_row1.addWidget(self.btn_show_stats)
        
        self.btn_save_data = QPushButton("Save Data")
        self.btn_save_data.clicked.connect(self.on_save_data)
        btn_row1.addWidget(self.btn_save_data)
        collection_layout.addLayout(btn_row1)
        
        # Buttons row 2
        btn_row2 = QHBoxLayout()
        self.btn_import_history = QPushButton("Import from History")
        self.btn_import_history.clicked.connect(self.on_import_history)
        self.btn_import_history.setToolTip("Import training data from current history")
        btn_row2.addWidget(self.btn_import_history)
        
        self.btn_clear_data = QPushButton("Clear All Data")
        self.btn_clear_data.clicked.connect(self.on_clear_data)
        btn_row2.addWidget(self.btn_clear_data)
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
        logger.info("ML Control Form initialized")
    
    def update_status(self):
        """Update status labels"""
        if self.ml_predictor.is_ready():
            self.lbl_model_status.setText("Model: ✓ Trained and ready")
            self.lbl_model_status.setStyleSheet("color: green; font-size: 11pt; font-weight: bold;")
            self.chk_use_ml.setEnabled(True)
        else:
            self.lbl_model_status.setText("Model: ✗ Not trained")
            self.lbl_model_status.setStyleSheet("color: red; font-size: 11pt;")
            self.chk_use_ml.setEnabled(False)
            self.chk_use_ml.setChecked(False)
        
        stats = self.ml_trainer.get_training_stats()
        total = sum(stats.values())
        
        if stats:
            details = ", ".join([f"{event}: {count}" for event, count in sorted(stats.items())])
            self.lbl_training_data.setText(f"Training samples: {total} ({details})")
        else:
            self.lbl_training_data.setText(f"Training samples: {total}")
        
        self.lbl_training_data.setStyleSheet("font-size: 11pt;")
    
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
        """Save training data to file"""
        try:
            self.ml_trainer.save_training_data()
            QMessageBox.information(
                self,
                "Success",
                f"Training data saved successfully.\n"
                f"File: {self.ml_trainer.config.training_data_path}"
            )
        except Exception as e:
            logger.error(f"Error saving training data: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to save training data:\n{e}")
    
    def on_clear_data(self):
        """Clear all training data"""
        reply = QMessageBox.question(
            self,
            "Confirm Clear",
            "Are you sure you want to clear all training data?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.ml_trainer.clear_training_data()
            self.update_status()
            logger.info("Training data cleared")
    
    def on_import_history(self):
        """Import training data from current history"""
        if not self.parent_window:
            QMessageBox.warning(self, "Error", "Cannot access parent window")
            return
        
        # Get history from parent window
        history_service = self.parent_window.history_service
        history_records = history_service.history
        
        if not history_records:
            QMessageBox.information(
                self,
                "No History",
                "History is empty. No data to import.\n\n"
                "Connect to BrainLink and collect some events first."
            )
            return
        
        # Show confirmation with preview
        total_records = len(history_records)
        with_events = sum(1 for r in history_records if hasattr(r, 'event_name') and r.event_name)
        
        reply = QMessageBox.question(
            self,
            "Import from History",
            f"Found {total_records} records in history.\n"
            f"Records with events: {with_events}\n\n"
            f"Import these records as training data?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            # Import from history
            imported, skipped = self.ml_trainer.import_from_history(history_records)
            
            # Update status
            self.update_status()
            
            # Show result
            QMessageBox.information(
                self,
                "Import Complete",
                f"Successfully imported {imported} samples from history.\n"
                f"Skipped {skipped} records (no event or invalid).\n\n"
                f"You can now train the model!"
            )
            
            logger.info(f"Imported {imported} samples from history")
        
        except Exception as e:
            logger.error(f"Error importing from history: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Import Failed",
                f"Failed to import from history:\n{e}"
            )
    
    def on_train_clicked(self):
        """Train the ML model"""
        # Check if can train
        can_train, reason = self.ml_trainer.can_train()
        if not can_train:
            QMessageBox.warning(
                self,
                "Cannot Train",
                f"Cannot train model:\n{reason}\n\n"
                f"Please collect more training data first."
            )
            return
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.btn_train.setEnabled(False)
        
        try:
            # Train model
            logger.info("Starting model training...")
            metrics = self.ml_trainer.train_model()
            
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
        
        except Exception as e:
            logger.error(f"Error training model: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Training Failed",
                f"Failed to train model:\n{e}"
            )
        
        finally:
            self.progress_bar.setVisible(False)
            self.btn_train.setEnabled(True)
    
    def on_use_ml_changed(self, state):
        """Handle use ML prediction checkbox"""
        if self.parent_window:
            self.parent_window._use_ml_prediction = (state == Qt.Checked)
            logger.info(f"ML prediction: {'enabled' if state == Qt.Checked else 'disabled'}")
