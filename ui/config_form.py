"""Configuration form for EEG fault tolerance settings"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QGroupBox, QFileDialog
)
from PyQt5.QtCore import Qt
import json
from pathlib import Path

from models.eeg_models import EegFaultModel
from .styles import apply_brainlink_style


class ConfigForm(QDialog):
    """Dialog for configuring EEG fault tolerance"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_window = parent
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Configuration")
        self.setGeometry(250, 250, 750, 450)
        
        # Apply dark theme
        apply_brainlink_style(self)
        
        layout = QVBoxLayout(self)
        
        # Main horizontal layout for Base and Multi groups (SIDE BY SIDE)
        groups_layout = QHBoxLayout()
        
        # Base fault tolerance group (LEFT)
        base_group = QGroupBox("Base Fault Tolerance")
        base_layout = QGridLayout()
        
        # Create input fields with DEFAULT VALUES from original BrainLinkConnect
        self.txt_attention = self._add_config_row(base_layout, "Attention:", 0, "5")
        self.txt_meditation = self._add_config_row(base_layout, "Meditation:", 1, "10")
        self.txt_delta = self._add_config_row(base_layout, "Delta:", 2, "300")
        self.txt_theta = self._add_config_row(base_layout, "Theta:", 3, "300")
        self.txt_low_alpha = self._add_config_row(base_layout, "Low Alpha:", 4, "0")
        self.txt_high_alpha = self._add_config_row(base_layout, "High Alpha:", 5, "0")
        self.txt_low_beta = self._add_config_row(base_layout, "Low Beta:", 6, "0")
        self.txt_high_beta = self._add_config_row(base_layout, "High Beta:", 7, "0")
        self.txt_low_gamma = self._add_config_row(base_layout, "Low Gamma:", 8, "0")
        self.txt_high_gamma = self._add_config_row(base_layout, "High Gamma:", 9, "0")
        
        base_group.setLayout(base_layout)
        groups_layout.addWidget(base_group)
        
        # Multi-level multiplier group (RIGHT)
        multi_group = QGroupBox("Multi-Level Multiplier")
        multi_layout = QGridLayout()
        
        # Default values from original BrainLinkConnect
        self.txt_attention_x = self._add_config_row(multi_layout, "Attention X:", 0, "1")
        self.txt_meditation_x = self._add_config_row(multi_layout, "Meditation X:", 1, "1")
        self.txt_delta_x = self._add_config_row(multi_layout, "Delta X:", 2, "3")
        self.txt_theta_x = self._add_config_row(multi_layout, "Theta X:", 3, "3")
        self.txt_low_alpha_x = self._add_config_row(multi_layout, "Low Alpha X:", 4, "3")
        self.txt_high_alpha_x = self._add_config_row(multi_layout, "High Alpha X:", 5, "3")
        self.txt_low_beta_x = self._add_config_row(multi_layout, "Low Beta X:", 6, "3")
        self.txt_high_beta_x = self._add_config_row(multi_layout, "High Beta X:", 7, "3")
        self.txt_low_gamma_x = self._add_config_row(multi_layout, "Low Gamma X:", 8, "3")
        self.txt_high_gamma_x = self._add_config_row(multi_layout, "High Gamma X:", 9, "3")
        
        multi_group.setLayout(multi_layout)
        groups_layout.addWidget(multi_group)
        
        # Add groups to main layout
        layout.addLayout(groups_layout)
        
        # Multi-level count
        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel("Multi Count:"))
        self.txt_multi_count = QLineEdit("1")
        count_layout.addWidget(self.txt_multi_count)
        layout.addLayout(count_layout)
        
        # File path for save/load
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("Config File:"))
        self.txt_filepath = QLineEdit("C:/BLconfig/config.json")
        file_layout.addWidget(self.txt_filepath)
        
        self.btn_browse = QPushButton("Browse")
        self.btn_browse.clicked.connect(self.on_browse_clicked)
        file_layout.addWidget(self.btn_browse)
        
        layout.addLayout(file_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.btn_load = QPushButton("Load Config")
        self.btn_load.clicked.connect(self.on_load_clicked)
        button_layout.addWidget(self.btn_load)
        
        self.btn_save = QPushButton("Save Config")
        self.btn_save.clicked.connect(self.on_save_clicked)
        button_layout.addWidget(self.btn_save)
        
        self.btn_ok = QPushButton("Apply")
        self.btn_ok.clicked.connect(self.on_ok_clicked)
        button_layout.addWidget(self.btn_ok)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.close)
        button_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(button_layout)
    
    def _add_config_row(self, layout: QGridLayout, label: str, row: int, default: str = "0") -> QLineEdit:
        """Add a configuration row to the layout"""
        layout.addWidget(QLabel(label), row, 0)
        txt_field = QLineEdit(default)
        layout.addWidget(txt_field, row, 1)
        return txt_field
    
    def get_config_fault(self) -> EegFaultModel:
        """Get base fault configuration from inputs"""
        try:
            return EegFaultModel(
                attention=int(self.txt_attention.text() or 0),
                meditation=int(self.txt_meditation.text() or 0),
                delta=int(self.txt_delta.text() or 0),
                theta=int(self.txt_theta.text() or 0),
                low_alpha=int(self.txt_low_alpha.text() or 0),
                high_alpha=int(self.txt_high_alpha.text() or 0),
                low_beta=int(self.txt_low_beta.text() or 0),
                high_beta=int(self.txt_high_beta.text() or 0),
                low_gamma=int(self.txt_low_gamma.text() or 0),
                high_gamma=int(self.txt_high_gamma.text() or 0)
            )
        except Exception as e:
            print(f"Error parsing config: {e}")
            return EegFaultModel()
    
    def get_config_fault_multi(self) -> EegFaultModel:
        """Get multiplier configuration from inputs"""
        try:
            return EegFaultModel(
                attention=int(self.txt_attention_x.text() or 1),
                meditation=int(self.txt_meditation_x.text() or 1),
                delta=int(self.txt_delta_x.text() or 1),
                theta=int(self.txt_theta_x.text() or 1),
                low_alpha=int(self.txt_low_alpha_x.text() or 1),
                high_alpha=int(self.txt_high_alpha_x.text() or 1),
                low_beta=int(self.txt_low_beta_x.text() or 1),
                high_beta=int(self.txt_high_beta_x.text() or 1),
                low_gamma=int(self.txt_low_gamma_x.text() or 1),
                high_gamma=int(self.txt_high_gamma_x.text() or 1)
            )
        except Exception as e:
            print(f"Error parsing multi config: {e}")
            return EegFaultModel()
    
    def get_multi_count(self) -> int:
        """Get multi-level count"""
        try:
            return int(self.txt_multi_count.text() or 1)
        except:
            return 1
    
    def on_ok_clicked(self):
        """Handle apply button click"""
        config = self.get_config_fault()
        config_multi = self.get_config_fault_multi()
        multi_count = self.get_multi_count()
        
        # Update parent window configuration
        if hasattr(self.parent_window, 'set_config_fault'):
            self.parent_window.set_config_fault(config, config_multi, multi_count)
        
        self.close()
    
    def on_browse_clicked(self):
        """Handle browse button click"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Select Config File",
            "C:/BLconfig",
            "JSON Files (*.json)"
        )
        if file_path:
            self.txt_filepath.setText(file_path)
    
    def on_load_clicked(self):
        """Handle load button click"""
        file_path = Path(self.txt_filepath.text())
        
        if not file_path.exists():
            print(f"File not found: {file_path}")
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                config = EegFaultModel.from_dict(data)
                
                # Update input fields
                self.txt_attention.setText(str(config.attention))
                self.txt_meditation.setText(str(config.meditation))
                self.txt_delta.setText(str(config.delta))
                self.txt_theta.setText(str(config.theta))
                self.txt_low_alpha.setText(str(config.low_alpha))
                self.txt_high_alpha.setText(str(config.high_alpha))
                self.txt_low_beta.setText(str(config.low_beta))
                self.txt_high_beta.setText(str(config.high_beta))
                self.txt_low_gamma.setText(str(config.low_gamma))
                self.txt_high_gamma.setText(str(config.high_gamma))
                
                print(f"Config loaded from {file_path}")
        except Exception as e:
            print(f"Error loading config: {e}")
    
    def on_save_clicked(self):
        """Handle save button click"""
        config = self.get_config_fault()
        file_path = Path(self.txt_filepath.text())
        
        try:
            # Create directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, indent=2)
                print(f"Config saved to {file_path}")
        except Exception as e:
            print(f"Error saving config: {e}")
