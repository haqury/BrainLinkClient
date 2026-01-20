"""Configuration form for EEG fault tolerance settings"""

import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QGroupBox, QFileDialog
)
from PyQt5.QtCore import Qt
import json
from pathlib import Path

from models.eeg_models import EegFaultModel
from config_defaults import DEFAULT_BASE_FAULT, DEFAULT_MULTI_FAULT, DEFAULT_MULTI_COUNT, DEFAULT_CONFIG_PATH
from .styles import apply_brainlink_style

logger = logging.getLogger(__name__)


class ConfigForm(QDialog):
    """Dialog for configuring EEG fault tolerance"""
    
    # Field names for EEG parameters (in order)
    EEG_FIELDS = [
        ('attention', 'Attention'),
        ('meditation', 'Meditation'),
        ('delta', 'Delta'),
        ('theta', 'Theta'),
        ('low_alpha', 'Low Alpha'),
        ('high_alpha', 'High Alpha'),
        ('low_beta', 'Low Beta'),
        ('high_beta', 'High Beta'),
        ('low_gamma', 'Low Gamma'),
        ('high_gamma', 'High Gamma'),
    ]
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_window = parent
        self.init_ui()
        # Load current configuration from parent window
        self.load_current_config()
    
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
        
        # Create all base fields dynamically
        for row, (field_name, label) in enumerate(self.EEG_FIELDS):
            default_value = str(getattr(DEFAULT_BASE_FAULT, field_name))
            field = self._add_config_row(base_layout, f"{label}:", row, default_value)
            setattr(self, f'txt_{field_name}', field)
        
        base_group.setLayout(base_layout)
        groups_layout.addWidget(base_group)
        
        # Multi-level multiplier group (RIGHT)
        multi_group = QGroupBox("Multi-Level Multiplier")
        multi_layout = QGridLayout()
        
        # Create all multiplier fields dynamically
        for row, (field_name, label) in enumerate(self.EEG_FIELDS):
            default_value = str(getattr(DEFAULT_MULTI_FAULT, field_name))
            field = self._add_config_row(multi_layout, f"{label} X:", row, default_value)
            setattr(self, f'txt_{field_name}_x', field)
        
        multi_group.setLayout(multi_layout)
        groups_layout.addWidget(multi_group)
        
        # Add groups to main layout
        layout.addLayout(groups_layout)
        
        # Multi-level count
        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel("Multi Count:"))
        self.txt_multi_count = QLineEdit(str(DEFAULT_MULTI_COUNT))
        count_layout.addWidget(self.txt_multi_count)
        layout.addLayout(count_layout)
        
        # File path for save/load
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("Config File:"))
        self.txt_filepath = QLineEdit(DEFAULT_CONFIG_PATH)
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
    
    def load_current_config(self):
        """Load current configuration from parent window"""
        if not hasattr(self.parent_window, 'config') or not self.parent_window.config:
            logger.info("Using default configuration values")
            return
        
        config = self.parent_window.config
        
        # Load base fault tolerance dynamically
        if config.eeg_fault:
            for field_name, _ in self.EEG_FIELDS:
                value = getattr(config.eeg_fault, field_name)
                field = getattr(self, f'txt_{field_name}')
                field.setText(str(value))
        
        # Load multipliers dynamically
        if config.eeg_fault_multi:
            for field_name, _ in self.EEG_FIELDS:
                value = getattr(config.eeg_fault_multi, field_name)
                field = getattr(self, f'txt_{field_name}_x')
                field.setText(str(value))
        
        # Load multi count
        self.txt_multi_count.setText(str(config.multi_count))
        
        logger.info(f"Loaded current configuration: multi_count={config.multi_count}")
    
    def get_config_fault(self) -> EegFaultModel:
        """Get base fault configuration from inputs"""
        try:
            values = {}
            for field_name, _ in self.EEG_FIELDS:
                field = getattr(self, f'txt_{field_name}')
                values[field_name] = int(field.text() or 0)
            
            return EegFaultModel(**values)
        except Exception as e:
            logger.error(f"Error parsing config: {e}")
            return EegFaultModel()
    
    def get_config_fault_multi(self) -> EegFaultModel:
        """Get multiplier configuration from inputs"""
        try:
            values = {}
            for field_name, _ in self.EEG_FIELDS:
                field = getattr(self, f'txt_{field_name}_x')
                values[field_name] = int(field.text() or 1)
            
            return EegFaultModel(**values)
        except Exception as e:
            logger.error(f"Error parsing multi config: {e}")
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
        """Handle load button click - loads full configuration"""
        file_path = Path(self.txt_filepath.text())
        
        if not file_path.exists():
            logger.warning(f"Config file not found: {file_path}")
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Check if it's a full config or just base fault (for backward compatibility)
                if "base_fault" in data:
                    # New format with full configuration
                    base_config = EegFaultModel.from_dict(data["base_fault"])
                    multi_config = EegFaultModel.from_dict(data.get("multi_fault", {}))
                    multi_count = data.get("multi_count", 1)
                    
                    # Update base fault fields dynamically
                    for field_name, _ in self.EEG_FIELDS:
                        value = getattr(base_config, field_name)
                        field = getattr(self, f'txt_{field_name}')
                        field.setText(str(value))
                    
                    # Update multiplier fields dynamically
                    for field_name, _ in self.EEG_FIELDS:
                        value = getattr(multi_config, field_name)
                        field = getattr(self, f'txt_{field_name}_x')
                        field.setText(str(value))
                    
                    # Update multi count
                    self.txt_multi_count.setText(str(multi_count))
                    
                    logger.info(f"Full config loaded from {file_path}")
                    logger.debug(f"Multi count: {multi_count}")
                else:
                    # Old format (only base fault) - for backward compatibility
                    config = EegFaultModel.from_dict(data)
                    
                    # Update only base fault fields dynamically
                    for field_name, _ in self.EEG_FIELDS:
                        value = getattr(config, field_name)
                        field = getattr(self, f'txt_{field_name}')
                        field.setText(str(value))
                    
                    logger.warning(f"Loaded old format config from {file_path} (base fault only)")
        except Exception as e:
            logger.error(f"Error loading config: {e}", exc_info=True)
    
    def on_save_clicked(self):
        """Handle save button click - saves full configuration"""
        base_config = self.get_config_fault()
        multi_config = self.get_config_fault_multi()
        multi_count = self.get_multi_count()
        file_path = Path(self.txt_filepath.text())
        
        try:
            # Create directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save complete configuration
            full_config = {
                "base_fault": base_config.to_dict(),
                "multi_fault": multi_config.to_dict(),
                "multi_count": multi_count
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(full_config, f, indent=2)
                logger.info(f"Config saved to {file_path}")
                logger.debug(f"Base fault: {base_config.to_dict()}")
                logger.debug(f"Multi fault: {multi_config.to_dict()}")
                logger.debug(f"Multi count: {multi_count}")
        except Exception as e:
            logger.error(f"Error saving config: {e}", exc_info=True)
