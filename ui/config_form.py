"""Configuration form for EEG fault tolerance settings"""

import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QGroupBox, QFileDialog
)
import json
from pathlib import Path

from models.eeg_models import EegFaultModel
from config_defaults import (
    DEFAULT_BASE_FAULT,
    DEFAULT_MULTI_FAULT,
    DEFAULT_MULTI_COUNT,
    get_default_config_path,
    save_fault_config,
)
from utils.brainlink_game_export import (
    save_fault_config_path,
    write_brainlink_export,
    load_fault_config_path,
)
from .styles import apply_brainlink_style

logger = logging.getLogger(__name__)


class ConfigForm(QDialog):
    """Dialog for configuring EEG fault tolerance"""

    # Includes signal so Apply/export match the game's 11-field fault UI
    EEG_FIELDS = [
        ('attention', 'Attention'),
        ('meditation', 'Meditation'),
        ('signal', 'Signal'),
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
        self.load_current_config()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Configuration")
        self.setGeometry(250, 250, 750, 500)

        apply_brainlink_style(self)

        layout = QVBoxLayout(self)
        groups_layout = QHBoxLayout()

        base_group = QGroupBox("Base Fault Tolerance")
        base_layout = QGridLayout()
        for row, (field_name, label) in enumerate(self.EEG_FIELDS):
            default_value = str(getattr(DEFAULT_BASE_FAULT, field_name))
            field = self._add_config_row(base_layout, f"{label}:", row, default_value)
            setattr(self, f'txt_{field_name}', field)
        base_group.setLayout(base_layout)
        groups_layout.addWidget(base_group)

        multi_group = QGroupBox("Multi-Level Multiplier")
        multi_layout = QGridLayout()
        for row, (field_name, label) in enumerate(self.EEG_FIELDS):
            default_value = str(getattr(DEFAULT_MULTI_FAULT, field_name))
            field = self._add_config_row(multi_layout, f"{label} X:", row, default_value)
            setattr(self, f'txt_{field_name}_x', field)
        multi_group.setLayout(multi_layout)
        groups_layout.addWidget(multi_group)

        layout.addLayout(groups_layout)

        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel("Multi Count:"))
        self.txt_multi_count = QLineEdit(str(DEFAULT_MULTI_COUNT))
        count_layout.addWidget(self.txt_multi_count)
        layout.addLayout(count_layout)

        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("Config File:"))
        initial_path = load_fault_config_path() or get_default_config_path()
        self.txt_filepath = QLineEdit(initial_path)
        file_layout.addWidget(self.txt_filepath)

        self.btn_browse = QPushButton("Browse")
        self.btn_browse.clicked.connect(self.on_browse_clicked)
        file_layout.addWidget(self.btn_browse)
        layout.addLayout(file_layout)

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
        layout.addWidget(QLabel(label), row, 0)
        txt_field = QLineEdit(default)
        layout.addWidget(txt_field, row, 1)
        return txt_field

    def _remember_fault_path(self, file_path: str) -> None:
        abs_path = str(Path(file_path).expanduser().resolve())
        self.txt_filepath.setText(abs_path)
        save_fault_config_path(abs_path)

    def load_current_config(self):
        if not hasattr(self.parent_window, 'config') or not self.parent_window.config:
            logger.info("Using default configuration values")
            return

        config = self.parent_window.config
        if config.eeg_fault:
            for field_name, _ in self.EEG_FIELDS:
                value = getattr(config.eeg_fault, field_name)
                getattr(self, f'txt_{field_name}').setText(str(value))
        if config.eeg_fault_multi:
            for field_name, _ in self.EEG_FIELDS:
                value = getattr(config.eeg_fault_multi, field_name)
                getattr(self, f'txt_{field_name}_x').setText(str(value))
        self.txt_multi_count.setText(str(config.multi_count))
        logger.info(f"Loaded current configuration: multi_count={config.multi_count}")

    def get_config_fault(self) -> EegFaultModel:
        try:
            values = {
                field_name: int(getattr(self, f'txt_{field_name}').text() or 0)
                for field_name, _ in self.EEG_FIELDS
            }
            return EegFaultModel(**values)
        except Exception as e:
            logger.error(f"Error parsing config: {e}")
            return EegFaultModel()

    def get_config_fault_multi(self) -> EegFaultModel:
        try:
            values = {
                field_name: int(getattr(self, f'txt_{field_name}_x').text() or 1)
                for field_name, _ in self.EEG_FIELDS
            }
            return EegFaultModel(**values)
        except Exception as e:
            logger.error(f"Error parsing multi config: {e}")
            return EegFaultModel()

    def get_multi_count(self) -> int:
        try:
            return int(self.txt_multi_count.text() or 1)
        except Exception:
            return 1

    def on_ok_clicked(self):
        config = self.get_config_fault()
        config_multi = self.get_config_fault_multi()
        multi_count = self.get_multi_count()
        file_path = self.txt_filepath.text().strip() or get_default_config_path()
        self._remember_fault_path(file_path)
        if hasattr(self.parent_window, 'set_config_fault'):
            self.parent_window.set_config_fault(config, config_multi, multi_count)
        self.close()

    def on_browse_clicked(self):
        from utils.path_utils import get_config_dir
        start_dir = self.txt_filepath.text().strip() or str(get_config_dir())
        dialog = QFileDialog(self, "Select Config File", start_dir, "JSON Files (*.json)")
        dialog.setFileMode(QFileDialog.AnyFile)
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        dialog.setOption(QFileDialog.DontConfirmOverwrite, True)
        if dialog.exec_():
            selected = dialog.selectedFiles()
            if selected:
                self.txt_filepath.setText(selected[0])

    def on_load_clicked(self):
        file_path = Path(self.txt_filepath.text().strip() or get_default_config_path())
        if not file_path.exists():
            logger.warning(f"Config file not found: {file_path}")
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if "base_fault" in data:
                base_config = EegFaultModel.from_dict(data["base_fault"])
                multi_config = EegFaultModel.from_dict(data.get("multi_fault", {}))
                multi_count = data.get("multi_count", 1)
                for field_name, _ in self.EEG_FIELDS:
                    getattr(self, f'txt_{field_name}').setText(str(getattr(base_config, field_name)))
                for field_name, _ in self.EEG_FIELDS:
                    getattr(self, f'txt_{field_name}_x').setText(str(getattr(multi_config, field_name)))
                self.txt_multi_count.setText(str(multi_count))
                logger.info(f"Full config loaded from {file_path}")
            else:
                config = EegFaultModel.from_dict(data)
                for field_name, _ in self.EEG_FIELDS:
                    getattr(self, f'txt_{field_name}').setText(str(getattr(config, field_name)))
                logger.warning(f"Loaded old format config from {file_path} (base fault only)")

            self._remember_fault_path(str(file_path))
            if hasattr(self.parent_window, "set_config_fault"):
                self.parent_window.set_config_fault(
                    self.get_config_fault(),
                    self.get_config_fault_multi(),
                    self.get_multi_count(),
                    persist=False,
                )
        except Exception as e:
            logger.error(f"Error loading config: {e}", exc_info=True)

    def on_save_clicked(self):
        base_config = self.get_config_fault()
        multi_config = self.get_config_fault_multi()
        multi_count = self.get_multi_count()
        file_path = self.txt_filepath.text().strip() or get_default_config_path()
        self._remember_fault_path(file_path)
        save_fault_config(base_config, multi_config, multi_count, path=file_path)

        if hasattr(self.parent_window, "set_config_fault"):
            self.parent_window.set_config_fault(
                base_config, multi_config, multi_count, persist=False
            )
        else:
            write_brainlink_export(self.parent_window)
