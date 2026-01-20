"""Main window for BrainLink Client application"""

import logging
import asyncio
import threading
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QCheckBox, QLineEdit, QFileDialog, QGroupBox, QMessageBox,
    QSystemTrayIcon, QComboBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from pynput import keyboard
from typing import Optional

# Using pybrainlink library for BrainLink device models
from pybrainlink import BrainLinkModel, BrainLinkExtendModel
from models.eeg_models import EegHistoryModel, ConfigParams, EegFaultModel
from models.event_types import EventType
from config_defaults import get_default_config, DEFAULT_HISTORY_PATH
from services.history_service import HistoryService
from services.mouse_service import MouseService
from services.head_tracker_service import HeadTracker
from services.system_service import SystemService
from services.ml_trainer_service import MLTrainerService
from services.ml_predictor_service import MLPredictorService
from services.device_manager_service import DeviceManagerService, DeviceInfo
from services.shared_memory_service import SharedMemoryService
from .styles import apply_brainlink_style
from .tray_icon import TrayIcon

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window"""
    
    # Signals for thread-safe UI updates
    eeg_data_updated = pyqtSignal(object)
    extend_data_updated = pyqtSignal(object)
    connection_error = pyqtSignal(str)  # Signal for connection errors
    connection_success = pyqtSignal(str)  # Signal for successful connection

    def __init__(self):
        super().__init__()
        
        # Services
        self.history_service = HistoryService()
        self.mouse_service = MouseService()
        self.head_tracker = HeadTracker()
        self.system_service = SystemService()
        self.device_manager = DeviceManagerService()
        
        # Shared Memory for game integration
        self.shared_memory = SharedMemoryService()
        
        # ML Services
        self.ml_trainer = MLTrainerService()
        self.ml_predictor = MLPredictorService(self.ml_trainer)
        self._use_ml_prediction = False  # Flag to switch between rule-based and ML prediction
        
        # Configuration - load defaults from config_defaults.py
        self.config = get_default_config()
        
        # Child windows
        self.connect_form = None
        self.eeg_data_form = None
        self.gyro_form = None
        self.config_form = None
        self.ml_control_form = None
        
        # ML training state
        self._is_collecting_training_data = False
        
        # Simulator
        self.simulator = None
        
        # State
        self.current_event = ""
        self.keyboard_listener: Optional[keyboard.Listener] = None
        self._minimize_to_tray = True  # Minimize to tray by default
        
        # Connection management
        self._connection_thread: Optional[threading.Thread] = None
        self._connection_loop: Optional[asyncio.AbstractEventLoop] = None
        self._is_connected = False
        
        # System tray
        self.tray_icon = TrayIcon(self)
        self.tray_icon.show_window.connect(self.show_from_tray)
        self.tray_icon.hide_window.connect(self.hide_to_tray)
        self.tray_icon.quit_app.connect(self.quit_application)
        
        # Setup UI
        self.init_ui()
        self.setup_keyboard_listener()
        
        # Connect signals
        self.eeg_data_updated.connect(self.on_eeg_data_updated)
        self.extend_data_updated.connect(self.on_extend_data_updated)
        self.connection_error.connect(self.on_connection_error)
        self.connection_success.connect(self.on_connection_success)
        
        # Device manager signals
        self.device_manager.devices_updated.connect(self.on_devices_updated)
        self.device_manager.scan_started.connect(self.on_scan_started)
        self.device_manager.scan_finished.connect(self.on_scan_finished)
        
        # Shared memory signals
        self.shared_memory.service_started.connect(self.on_shm_started)
        self.shared_memory.service_stopped.connect(self.on_shm_stopped)
        self.shared_memory.error_occurred.connect(self.on_shm_error)
        self.shared_memory.command_received.connect(self.on_shm_command_received)
        
        # Show tray icon
        self.tray_icon.show()
        
        logger.info("MainWindow initialized with system tray")
        
        # Initialize devices on startup
        QTimer.singleShot(500, self.initialize_devices)

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("BrainLink Client")
        self.setGeometry(100, 100, 800, 600)
        
        # Apply dark theme with GreenYellow accents
        apply_brainlink_style(self)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Connection section
        connection_group = QGroupBox("Connection")
        connection_layout = QHBoxLayout()
        
        connection_layout.addWidget(QLabel("Device:"))
        
        self.cmb_devices = QComboBox()
        self.cmb_devices.setMinimumWidth(250)
        self.cmb_devices.currentIndexChanged.connect(self.on_device_selected)
        connection_layout.addWidget(self.cmb_devices)
        
        self.btn_rescan = QPushButton("🔄 Rescan")
        self.btn_rescan.setToolTip("Rescan for Bluetooth devices")
        self.btn_rescan.clicked.connect(self.on_rescan_clicked)
        connection_layout.addWidget(self.btn_rescan)
        
        self.btn_disconnect = QPushButton("Disconnect")
        self.btn_disconnect.setEnabled(False)
        self.btn_disconnect.clicked.connect(self.disconnect_device)
        connection_layout.addWidget(self.btn_disconnect)
        
        connection_layout.addStretch()
        
        connection_group.setLayout(connection_layout)
        main_layout.addWidget(connection_group)
        
        # Extended data section
        extend_group = QGroupBox("Extended Data")
        extend_layout = QHBoxLayout()
        
        extend_layout.addWidget(QLabel("AP:"))
        self.lbl_ap = QLabel("0")
        extend_layout.addWidget(self.lbl_ap)
        
        extend_layout.addWidget(QLabel("Electric:"))
        self.lbl_electric = QLabel("0")
        extend_layout.addWidget(self.lbl_electric)
        
        extend_layout.addWidget(QLabel("Version:"))
        self.lbl_version = QLabel("0")
        extend_layout.addWidget(self.lbl_version)
        
        extend_layout.addWidget(QLabel("Temp:"))
        self.lbl_temp = QLabel("0")
        extend_layout.addWidget(self.lbl_temp)
        
        extend_layout.addWidget(QLabel("Heart:"))
        self.lbl_heart = QLabel("0")
        extend_layout.addWidget(self.lbl_heart)
        
        extend_group.setLayout(extend_layout)
        main_layout.addWidget(extend_group)
        
        # Event selection section
        event_group = QGroupBox("Event Selection (Training Mode)")
        event_layout = QHBoxLayout()
        
        self.cb_ml = QCheckBox("Move Left")
        self.cb_mr = QCheckBox("Move Right")
        self.cb_mu = QCheckBox("Move Up")
        self.cb_md = QCheckBox("Move Down")
        self.cb_stop = QCheckBox("Stop")
        
        event_layout.addWidget(self.cb_ml)
        event_layout.addWidget(self.cb_mr)
        event_layout.addWidget(self.cb_mu)
        event_layout.addWidget(self.cb_md)
        event_layout.addWidget(self.cb_stop)
        
        event_group.setLayout(event_layout)
        main_layout.addWidget(event_group)
        
        # Control options
        control_group = QGroupBox("Control Options")
        control_layout = QHBoxLayout()
        
        self.cb_autouse = QCheckBox("Auto Use (Direct Control)")
        self.cb_use_key = QCheckBox("Use Key Control")
        self.chk_minimize_to_tray = QCheckBox("Minimize to tray")
        self.chk_minimize_to_tray.setChecked(True)
        self.chk_minimize_to_tray.setToolTip("Minimize to system tray instead of closing")
        self.chk_minimize_to_tray.stateChanged.connect(self.on_minimize_to_tray_changed)
        
        control_layout.addWidget(self.cb_autouse)
        control_layout.addWidget(self.cb_use_key)
        control_layout.addWidget(self.chk_minimize_to_tray)
        
        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)
        
        # Shared Memory section (for game integration)
        shm_group = QGroupBox("Game Integration (Shared Memory)")
        shm_layout = QHBoxLayout()
        
        self.chk_enable_shm = QCheckBox("Enable Shared Memory")
        self.chk_enable_shm.setToolTip("Ultra-fast game integration via shared memory (~0.01ms latency)")
        self.chk_enable_shm.stateChanged.connect(self.on_shm_toggled)
        shm_layout.addWidget(self.chk_enable_shm)
        
        self.lbl_shm_status = QLabel("Status: Stopped")
        self.lbl_shm_status.setStyleSheet("color: #888;")
        shm_layout.addWidget(self.lbl_shm_status)
        
        self.lbl_shm_updates = QLabel("Updates: 0")
        shm_layout.addWidget(self.lbl_shm_updates)
        
        shm_layout.addStretch()
        
        shm_group.setLayout(shm_layout)
        main_layout.addWidget(shm_group)
        
        # History section
        history_group = QGroupBox("History Management")
        history_layout = QVBoxLayout()
        
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("File Path:"))
        self.txt_filepath = QLineEdit(DEFAULT_HISTORY_PATH)
        file_layout.addWidget(self.txt_filepath)
        
        self.btn_browse = QPushButton("Browse")
        self.btn_browse.clicked.connect(self.on_browse_clicked)
        file_layout.addWidget(self.btn_browse)
        
        history_layout.addLayout(file_layout)
        
        history_buttons = QHBoxLayout()
        
        self.btn_save = QPushButton("Save to File")
        self.btn_save.clicked.connect(self.on_save_clicked)
        history_buttons.addWidget(self.btn_save)
        
        self.btn_load = QPushButton("Load from File")
        self.btn_load.clicked.connect(self.on_load_clicked)
        history_buttons.addWidget(self.btn_load)
        
        self.btn_clear = QPushButton("Clear")
        self.btn_clear.clicked.connect(self.on_clear_clicked)
        history_buttons.addWidget(self.btn_clear)
        
        history_layout.addLayout(history_buttons)
        
        counter_layout = QHBoxLayout()
        counter_layout.addWidget(QLabel("Records:"))
        self.lbl_counter = QLabel("0")
        counter_layout.addWidget(self.lbl_counter)
        counter_layout.addStretch()
        
        history_layout.addLayout(counter_layout)
        
        history_group.setLayout(history_layout)
        main_layout.addWidget(history_group)
        
        # Windows section
        windows_group = QGroupBox("Data Windows")
        windows_layout = QHBoxLayout()
        
        self.btn_config = QPushButton("Config Fault")
        self.btn_config.clicked.connect(self.on_config_clicked)
        windows_layout.addWidget(self.btn_config)
        
        self.btn_eeg_data = QPushButton("EEG Data")
        self.btn_eeg_data.clicked.connect(self.on_eeg_data_clicked)
        windows_layout.addWidget(self.btn_eeg_data)
        
        self.btn_gyro = QPushButton("Gyro")
        self.btn_gyro.clicked.connect(self.on_gyro_clicked)
        windows_layout.addWidget(self.btn_gyro)
        
        self.btn_ml_control = QPushButton("ML Control")
        self.btn_ml_control.clicked.connect(self.on_ml_control_clicked)
        self.btn_ml_control.setToolTip("Open ML model training and control")
        windows_layout.addWidget(self.btn_ml_control)
        
        windows_group.setLayout(windows_layout)
        main_layout.addWidget(windows_group)
        
        main_layout.addStretch()

    def setup_keyboard_listener(self):
        """Setup global keyboard listener"""
        def on_press(key):
            """Handle key press events"""
            try:
                if key == keyboard.Key.left:
                    self.cb_ml.setChecked(True)
                elif key == keyboard.Key.right:
                    self.cb_mr.setChecked(True)
                elif key == keyboard.Key.up:
                    self.cb_mu.setChecked(True)
                elif key == keyboard.Key.down:
                    self.cb_md.setChecked(True)
            except:
                pass
        
        def on_release(key):
            """Handle key release events"""
            try:
                if key == keyboard.Key.left:
                    self.cb_ml.setChecked(False)
                elif key == keyboard.Key.right:
                    self.cb_mr.setChecked(False)
                elif key == keyboard.Key.up:
                    self.cb_mu.setChecked(False)
                elif key == keyboard.Key.down:
                    self.cb_md.setChecked(False)
            except:
                pass
        
        self.keyboard_listener = keyboard.Listener(
            on_press=on_press,
            on_release=on_release
        )
        self.keyboard_listener.start()

    def initialize_devices(self):
        """Initialize device list on startup"""
        # Check if Bluetooth is available
        bt_available, bt_message = DeviceManagerService.check_bluetooth_available()
        
        if not bt_available:
            logger.warning(f"Bluetooth not available: {bt_message}")
            reply = QMessageBox.question(
                self,
                "Bluetooth Not Available",
                f"{bt_message}\n\n"
                f"Would you like to enable Bluetooth?\n\n"
                f"Note: You may need to enable it in Windows Settings.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                QMessageBox.information(
                    self,
                    "Enable Bluetooth",
                    "Please enable Bluetooth in Windows Settings.\n\n"
                    "After enabling, click 'Rescan' button to search for devices."
                )
        
        # Start initial scan
        logger.info("Starting initial device scan...")
        self.device_manager.start_scan()
    
    def on_devices_updated(self, devices: list):
        """Handle device list update"""
        logger.info(f"Devices updated: {len(devices)} devices")
        
        # Block signals while updating
        self.cmb_devices.blockSignals(True)
        
        # Remember current selection
        current_address = None
        if self.cmb_devices.currentIndex() >= 0:
            current_data = self.cmb_devices.currentData()
            if current_data:
                current_address = current_data.address
        
        # Clear and repopulate
        self.cmb_devices.clear()
        
        for device in devices:
            self.cmb_devices.addItem(str(device), device)
        
        # Try to restore selection
        if current_address:
            for i in range(self.cmb_devices.count()):
                device = self.cmb_devices.itemData(i)
                if device and device.address == current_address:
                    self.cmb_devices.setCurrentIndex(i)
                    break
        else:
            # Select last device if available
            last_device = self.device_manager.get_last_device()
            if last_device:
                for i in range(self.cmb_devices.count()):
                    device = self.cmb_devices.itemData(i)
                    if device and device.address == last_device.address:
                        self.cmb_devices.setCurrentIndex(i)
                        logger.info(f"Selected last device: {last_device}")
                        break
        
        # Unblock signals
        self.cmb_devices.blockSignals(False)
        
        # Auto-connect if scan just finished and we have a selection
        if self.cmb_devices.currentIndex() >= 0:
            selected_device = self.cmb_devices.currentData()
            if selected_device and not selected_device.is_simulator:
                # Auto-connect after scan if not simulator
                last_device = self.device_manager.get_last_device()
                if last_device and last_device.address == selected_device.address:
                    logger.info(f"Auto-connecting to last device: {selected_device}")
                    QTimer.singleShot(1000, lambda: self.on_device_selected(self.cmb_devices.currentIndex()))
    
    def on_scan_started(self):
        """Handle scan start"""
        self.btn_rescan.setEnabled(False)
        self.btn_rescan.setText("🔄 Scanning...")
        self.cmb_devices.setEnabled(False)
        logger.info("Device scan started")
    
    def on_scan_finished(self):
        """Handle scan finish"""
        self.btn_rescan.setEnabled(True)
        self.btn_rescan.setText("🔄 Rescan")
        self.cmb_devices.setEnabled(True)
        logger.info("Device scan finished")
    
    def on_device_selected(self, index: int):
        """Handle device selection - auto connect"""
        if index < 0:
            return
        
        device = self.cmb_devices.itemData(index)
        if not device:
            return
        
        logger.info(f"Device selected: {device}")
        
        # Save as last device
        self.device_manager.save_last_device(device)
        
        # Disconnect if already connected
        if self._is_connected:
            logger.info("Disconnecting previous device before connecting new one")
            self.disconnect_device()
            # Wait a bit before connecting
            QTimer.singleShot(500, lambda: self._connect_to_device(device))
        else:
            self._connect_to_device(device)
    
    def _connect_to_device(self, device: DeviceInfo):
        """Internal method to connect to selected device"""
        if device.is_simulator:
            # Connect to simulator
            logger.info("Connecting to simulator...")
            from services.device_simulator import SimulatorController
            self.simulator = SimulatorController(self)
            self.simulator.connect()
            
            QMessageBox.information(
                self,
                "Simulator Started",
                "✅ Device simulator is now running!\n\n"
                "You should see EEG data updating."
            )
        else:
            # Connect to real device
            logger.info(f"Connecting to real device: {device.address}")
            self.connect_device(device.address)
    
    def on_rescan_clicked(self):
        """Handle rescan button click"""
        logger.info("Rescan requested")
        self.device_manager.start_scan()

    def on_minimize_to_tray_changed(self, state):
        """Handle minimize to tray checkbox state change"""
        self._minimize_to_tray = (state == Qt.Checked)
        logger.info(f"Minimize to tray: {'enabled' if self._minimize_to_tray else 'disabled'}")
    
    def on_browse_clicked(self):
        """Handle browse button click"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Select History File",
            "C:/BLconfig",
            "JSON Files (*.json)"
        )
        if file_path:
            self.txt_filepath.setText(file_path)

    def on_save_clicked(self):
        """Handle save button click"""
        self.history_service.save(self.txt_filepath.text())
        self.update_counter()

    def on_load_clicked(self):
        """Handle load button click"""
        self.history_service.load(self.txt_filepath.text())
        self.update_counter()

    def on_clear_clicked(self):
        """Handle clear button click"""
        self.history_service.clear()
        self.update_counter()

    def on_config_clicked(self):
        """Handle config button click"""
        from ui.config_form import ConfigForm
        self.config_form = ConfigForm(self)
        self.config_form.show()

    def on_eeg_data_clicked(self):
        """Handle EEG data button click"""
        if self.eeg_data_form is None:
            from ui.eeg_data_form import EEGDataForm
            self.eeg_data_form = EEGDataForm()
        self.eeg_data_form.show()

    def on_gyro_clicked(self):
        """Handle gyro button click"""
        if self.gyro_form is None:
            from ui.gyro_form import GyroForm
            self.gyro_form = GyroForm(self.head_tracker)
        self.gyro_form.show()
    
    def on_ml_control_clicked(self):
        """Handle ML control button click - opens separate window"""
        if self.ml_control_form is None or not self.ml_control_form.isVisible():
            from ui.ml_control_form import MLControlForm
            self.ml_control_form = MLControlForm(self.ml_trainer, self.ml_predictor, self)
            self.ml_control_form.show()
        else:
            # Bring existing window to front
            self.ml_control_form.raise_()
            self.ml_control_form.activateWindow()
        
        self.ml_control_form.update_status()

    def on_shm_toggled(self, state):
        """Handle shared memory toggle"""
        if state == Qt.Checked:
            try:
                self.shared_memory.start()
            except Exception as e:
                logger.error(f"Failed to start shared memory service: {e}", exc_info=True)
                self.chk_enable_shm.setChecked(False)
                QMessageBox.critical(
                    self,
                    "Shared Memory Error",
                    f"Failed to start shared memory service:\n{e}\n\n"
                    f"This feature requires Python multiprocessing support."
                )
        else:
            self.shared_memory.stop()
    
    def on_shm_started(self, memory_name: str):
        """Handle shared memory service started"""
        self.lbl_shm_status.setText(f"Status: Running ('{memory_name}')")
        self.lbl_shm_status.setStyleSheet("color: green; font-weight: bold;")
        logger.info(f"Shared memory service started: {memory_name}")
        
        # Show notification
        self.tray_icon.show_message(
            "Shared Memory",
            f"Game integration enabled (memory: '{memory_name}')\n"
            f"Latency: ~0.01-0.05ms",
            QSystemTrayIcon.Information
        )
    
    def on_shm_stopped(self):
        """Handle shared memory service stopped"""
        self.lbl_shm_status.setText("Status: Stopped")
        self.lbl_shm_status.setStyleSheet("color: #888;")
        self.lbl_shm_updates.setText("Updates: 0")
        logger.info("Shared memory service stopped")
    
    def on_shm_error(self, error_msg: str):
        """Handle shared memory error"""
        logger.error(f"Shared memory error: {error_msg}")
        QMessageBox.warning(
            self,
            "Shared Memory Error",
            f"Shared memory error:\n{error_msg}"
        )
    
    def on_shm_command_received(self, command: dict):
        """Handle command received from game client via shared memory"""
        try:
            command_type = command.get("type", 0)
            event_name = command.get("event", "")
            
            if not event_name:
                logger.warning("Received command with empty event name")
                return
            
            logger.info(f"Processing command from game: type={command_type}, event={event_name}")
            
            # Type 1: Save event to history
            if command_type == 1:
                # Get current EEG data from device
                if hasattr(self, 'device') and self.device and hasattr(self.device, 'model'):
                    model = self.device.model
                    
                    # Create history record with event
                    from models.eeg_models import EegHistoryModel
                    h = EegHistoryModel(
                        attention=model.attention,
                        meditation=model.meditation,
                        delta=model.delta,
                        theta=model.theta,
                        low_alpha=model.low_alpha,
                        high_alpha=model.high_alpha,
                        low_beta=model.low_beta,
                        high_beta=model.high_beta,
                        low_gamma=model.low_gamma,
                        high_gamma=model.high_gamma,
                        event_name=event_name
                    )
                    
                    self.history_service.add(h)
                    self.update_counter()
                    logger.info(f"Saved event '{event_name}' to history from game")
                    
                    # Update status in tray
                    self.tray_icon.show_message(
                        "Event Saved",
                        f"Game saved event: {event_name}",
                        QSystemTrayIcon.Information
                    )
                else:
                    logger.warning("No active device, cannot save event with current EEG data")
            
            # Type 2: Save for ML training
            elif command_type == 2:
                # Get current EEG data
                if hasattr(self, 'device') and self.device and hasattr(self.device, 'model'):
                    model = self.device.model
                    
                    # Create training sample
                    from models.ml_models import MLTrainingData
                    training_sample = MLTrainingData(
                        attention=model.attention,
                        meditation=model.meditation,
                        delta=model.delta,
                        theta=model.theta,
                        low_alpha=model.low_alpha,
                        high_alpha=model.high_alpha,
                        low_beta=model.low_beta,
                        high_beta=model.high_beta,
                        low_gamma=model.low_gamma,
                        high_gamma=model.high_gamma,
                        event=event_name
                    )
                    
                    self.ml_trainer.add_training_sample(training_sample)
                    logger.info(f"Added ML training sample '{event_name}' from game")
                    
                    # Also save to history
                    h = EegHistoryModel(
                        attention=model.attention,
                        meditation=model.meditation,
                        delta=model.delta,
                        theta=model.theta,
                        low_alpha=model.low_alpha,
                        high_alpha=model.high_alpha,
                        low_beta=model.low_beta,
                        high_beta=model.high_beta,
                        low_gamma=model.low_gamma,
                        high_gamma=model.high_gamma,
                        event_name=event_name
                    )
                    self.history_service.add(h)
                    self.update_counter()
                    
                    self.tray_icon.show_message(
                        "ML Training Data",
                        f"Game added training sample: {event_name}",
                        QSystemTrayIcon.Information
                    )
                else:
                    logger.warning("No active device, cannot save ML training data")
            
            else:
                logger.warning(f"Unknown command type: {command_type}")
        
        except Exception as e:
            logger.error(f"Error processing shared memory command: {e}", exc_info=True)
    
    def update_counter(self):
        """Update history counter display"""
        self.lbl_counter.setText(str(self.history_service.count()))

    def get_event_name(self) -> str:
        """Get currently selected event name using EventType enum"""
        if self.cb_ml.isChecked():
            return EventType.MOVE_LEFT.value
        elif self.cb_mr.isChecked():
            return EventType.MOVE_RIGHT.value
        elif self.cb_mu.isChecked():
            return EventType.MOVE_UP.value
        elif self.cb_md.isChecked():
            return EventType.MOVE_DOWN.value
        elif self.cb_stop.isChecked():
            return EventType.STOP.value
        return ""

    def set_config_fault(self, config: EegFaultModel, config_multi: EegFaultModel, multi_count: int):
        """Set configuration from config form"""
        self.config.eeg_fault = config
        self.config.eeg_faults = [config]
        
        # Generate multi-level faults
        for i in range(1, multi_count):
            prev_fault = self.config.eeg_faults[i - 1]
            new_fault = EegFaultModel(
                attention=int(prev_fault.attention * config_multi.attention),
                meditation=int(prev_fault.meditation * config_multi.meditation),
                low_alpha=int(prev_fault.low_alpha * config_multi.low_alpha),
                low_beta=int(prev_fault.low_beta * config_multi.low_beta),
                low_gamma=int(prev_fault.low_gamma * config_multi.low_gamma),
                high_alpha=int(prev_fault.high_alpha * config_multi.high_alpha),
                high_beta=int(prev_fault.high_beta * config_multi.high_beta),
                high_gamma=int(prev_fault.high_gamma * config_multi.high_gamma),
                delta=int(prev_fault.delta * config_multi.delta),
                theta=int(prev_fault.theta * config_multi.theta)
            )
            self.config.eeg_faults.append(new_fault)
        
        self.config.multi_count = multi_count
        logger.info(f"Config updated: multi_count={multi_count}")

    def connect_device(self, address: str):
        """Connect to BrainLink device via pybrainlink with proper error handling"""
        logger.info(f"Connecting to device: {address}")
        logger.info("Using PyBrainLink library for Bluetooth connection")
        
        # Disconnect previous connection if exists
        if self._is_connected:
            logger.warning("Disconnecting previous connection before new one")
            self.disconnect_device()
        
        # Import pybrainlink
        from pybrainlink import BrainLinkDevice
        
        def connect_async():
            """Async connection function with proper exception handling"""
            loop = None
            device = None
            
            try:
                # Create new event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                self._connection_loop = loop
                
                logger.debug("Creating BrainLinkDevice instance")
                device = BrainLinkDevice()
                device.on_eeg_data = self.on_eeg_data_event
                device.on_extend_data = self.on_extend_data_event
                device.on_gyro_data = self.on_gyro_data_event  # Always connect gyro callback
                
                logger.info(f"Attempting to connect to device: {address}")
                
                # Connect to device
                loop.run_until_complete(device.connect(address))
                
                self._is_connected = True
                logger.info(f"Successfully connected to device: {address}")
                self.connection_success.emit(address)
                
                # Keep connection alive
                loop.run_forever()
                
            except asyncio.CancelledError:
                logger.info("Connection cancelled by user")
                
            except Exception as e:
                error_msg = f"Connection error: {str(e)}"
                logger.error(error_msg, exc_info=True)
                self.connection_error.emit(error_msg)
                
            finally:
                # Clean up
                logger.debug("Cleaning up connection resources")
                self._is_connected = False
                
                if device:
                    try:
                        if loop and loop.is_running():
                            loop.run_until_complete(device.disconnect())
                    except Exception as e:
                        logger.error(f"Error disconnecting device: {e}")
                
                if loop:
                    try:
                        loop.close()
                    except Exception as e:
                        logger.error(f"Error closing event loop: {e}")
                
                self._connection_loop = None
                logger.info("Connection thread terminated")
        
        # Start connection thread
        self._connection_thread = threading.Thread(target=connect_async, daemon=True, name="BLE-Connection")
        self._connection_thread.start()
        logger.debug("Connection thread started")

    def disconnect_device(self):
        """Disconnect from device and clean up resources"""
        logger.info("Disconnecting from device")
        
        # Update UI
        self.btn_disconnect.setEnabled(False)
        self.cmb_devices.setEnabled(True)
        
        if self._connection_loop and self._connection_loop.is_running():
            try:
                logger.debug("Stopping connection event loop")
                self._connection_loop.call_soon_threadsafe(self._connection_loop.stop)
            except Exception as e:
                logger.error(f"Error stopping event loop: {e}")
        
        if self._connection_thread and self._connection_thread.is_alive():
            logger.debug("Waiting for connection thread to terminate")
            self._connection_thread.join(timeout=2.0)
            if self._connection_thread.is_alive():
                logger.warning("Connection thread did not terminate gracefully")
        
        self._is_connected = False
        self._connection_thread = None
        self._connection_loop = None
        
        # Update tray status
        self.tray_icon.update_status(connected=False)
        
        logger.info("Device disconnected")
    
    def on_connection_error(self, error_msg: str):
        """Handle connection error signal (called in main thread)"""
        logger.error(f"Connection error in UI: {error_msg}")
        QMessageBox.critical(
            self,
            "Connection Error",
            f"Failed to connect to device:\n\n{error_msg}\n\nCheck logs for details."
        )
        
        # Update tray status and notification
        self.tray_icon.update_status(connected=False)
        self.tray_icon.show_message(
            "BrainLink Client",
            f"Connection failed",
            QSystemTrayIcon.Critical
        )
    
    def on_connection_success(self, address: str):
        """Handle successful connection signal (called in main thread)"""
        logger.info(f"Connection successful in UI: {address}")
        
        # Update UI
        self.btn_disconnect.setEnabled(True)
        self.cmb_devices.setEnabled(False)  # Disable device selection while connected
        
        QMessageBox.information(
            self,
            "Connected",
            f"Successfully connected to device:\n{address}"
        )
        
        # Update tray status and notification
        self.tray_icon.update_status(connected=True)
        self.tray_icon.show_message(
            "BrainLink Client",
            f"Connected to {address}",
            QSystemTrayIcon.Information
        )
    
    def on_eeg_data_event(self, model: BrainLinkModel):
        """Handle EEG data event (called from device)"""
        self.eeg_data_updated.emit(model)

    def on_eeg_data_updated(self, model: BrainLinkModel):
        """Handle EEG data in main thread"""
        # Get event name (rule-based or ML-based)
        event_name = self.get_event_name()  # Default: rule-based
        
        # Use ML prediction if enabled
        if self._use_ml_prediction and self.ml_predictor.is_ready():
            prediction = self.ml_predictor.predict(model)
            if prediction and prediction.is_confident(self.ml_trainer.config.confidence_threshold):
                event_name = prediction.predicted_event
                logger.debug(f"ML predicted event: {event_name} (confidence: {prediction.confidence:.2f})")
            else:
                logger.debug("ML prediction not confident enough, using rule-based")
                event_name = self.get_event_name()
        
        # Create history record
        h = EegHistoryModel(
            attention=model.attention,
            meditation=model.meditation,
            delta=model.delta,
            theta=model.theta,
            low_alpha=model.low_alpha,
            high_alpha=model.high_alpha,
            low_beta=model.low_beta,
            high_beta=model.high_beta,
            low_gamma=model.low_gamma,
            high_gamma=model.high_gamma,
            event_name=event_name
        )
        
        # Process mouse control
        if self.cb_autouse.isChecked() and h.event_name:
            self.mouse_service.play(h, self.config, h.event_name, self.cb_use_key.isChecked())
        else:
            event_name = self.history_service.get_event_name_by(h, self.config)
            self.mouse_service.play(h, self.config, event_name, self.cb_use_key.isChecked())
        
        # Update EEG data form if open
        if self.eeg_data_form and self.eeg_data_form.isVisible():
            self.eeg_data_form.update_data(model)
        
        # Add to history if event is set
        if h.event_name:
            self.history_service.add(h)
        
        # Collect training data if in training mode
        if hasattr(self, '_is_collecting_training_data') and self._is_collecting_training_data and event_name:
            from models.ml_models import MLTrainingData
            training_sample = MLTrainingData(
                attention=model.attention,
                meditation=model.meditation,
                delta=model.delta,
                theta=model.theta,
                low_alpha=model.low_alpha,
                high_alpha=model.high_alpha,
                low_beta=model.low_beta,
                high_beta=model.high_beta,
                low_gamma=model.low_gamma,
                high_gamma=model.high_gamma,
                event=event_name
            )
            self.ml_trainer.add_training_sample(training_sample)
            logger.debug(f"Added training sample for event: {event_name}")
            self.update_counter()
        
        # Update shared memory if enabled
        if self.shared_memory.is_running:
            eeg_data = {
                "attention": model.attention,
                "meditation": model.meditation,
                "signal": model.signal,
                "delta": model.delta,
                "theta": model.theta,
                "low_alpha": model.low_alpha,
                "high_alpha": model.high_alpha,
                "low_beta": model.low_beta,
                "high_beta": model.high_beta,
                "low_gamma": model.low_gamma,
                "high_gamma": model.high_gamma,
                "event": event_name
            }
            self.shared_memory.update_eeg_data(eeg_data)
            
            # Update UI counter
            stats = self.shared_memory.get_stats()
            self.lbl_shm_updates.setText(f"Updates: {stats['updates_sent']}")

    def on_extend_data_event(self, model: BrainLinkExtendModel):
        """Handle extended data event (called from device)"""
        logger.info(f"🔵 Extended data received from device:")
        logger.info(f"   AP: {model.ap}")
        logger.info(f"   Electric: {model.electric}")
        logger.info(f"   Version: '{model.version}'")
        logger.info(f"   Temperature: {model.temperature}")
        logger.info(f"   Heart Rate: {model.heart_rate}")
        logger.debug(f"   Raw model: {model.__dict__ if hasattr(model, '__dict__') else model}")
        self.extend_data_updated.emit(model)

    def on_extend_data_updated(self, model: BrainLinkExtendModel):
        """Handle extended data in main thread"""
        logger.debug(f"Updating UI with extended data: ap={model.ap}, electric={model.electric}")
        self.lbl_ap.setText(str(model.ap))
        self.lbl_electric.setText(str(model.electric))
        self.lbl_version.setText(model.version)
        self.lbl_temp.setText(str(model.temperature))
        self.lbl_heart.setText(str(model.heart_rate))
        
        # Update shared memory if enabled
        if self.shared_memory.is_running:
            self.shared_memory.update_extended_data(
                ap=model.ap,
                electric=model.electric,
                temp=model.temperature,
                heart=model.heart_rate
            )
    
    def on_gyro_data_event(self, x: int, y: int, z: int):
        """Handle gyro data event (called from device) - forward to gyro form if it exists"""
        logger.debug(f"Gyro data received: X={x}, Y={y}, Z={z}")
        if self.gyro_form:
            self.gyro_form.update_gyro_data(x, y, z)
        else:
            logger.debug("Gyro form not open - data not displayed")
        
        # Update shared memory if enabled
        if self.shared_memory.is_running:
            self.shared_memory.update_gyro_data(x, y, z)

    def closeEvent(self, event):
        """Handle window close event - minimize to tray or quit"""
        if self._minimize_to_tray:
            # Minimize to tray instead of closing
            event.ignore()
            self.hide_to_tray()
            logger.info("Window minimized to tray")
        else:
            # Actually quit the application
            self.quit_application()
            event.accept()
    
    def hide_to_tray(self):
        """Hide window to system tray"""
        self.hide()
        self.tray_icon.show_message(
            "BrainLink Client",
            "Application minimized to tray. Double-click tray icon to restore.",
            QSystemTrayIcon.Information,
            2000
        )
        logger.info("Window hidden to tray")
    
    def show_from_tray(self):
        """Show window from system tray"""
        self.show()
        self.activateWindow()
        self.raise_()
        logger.info("Window restored from tray")
    
    def quit_application(self):
        """Properly quit the application with cleanup"""
        logger.info("Application closing - cleaning up resources")
        
        try:
            # Stop device connection
            if self._is_connected:
                logger.info("Disconnecting from device")
                self.disconnect_device()
            
            # Stop keyboard listener
            if self.keyboard_listener:
                logger.info("Stopping keyboard listener")
                try:
                    self.keyboard_listener.stop()
                except Exception as e:
                    logger.error(f"Error stopping keyboard listener: {e}")
            
            # Stop mouse service
            logger.info("Stopping mouse service")
            try:
                self.mouse_service.stop()
            except Exception as e:
                logger.error(f"Error stopping mouse service: {e}")
            
            # Stop simulator if running
            if self.simulator:
                logger.info("Stopping simulator")
                try:
                    self.simulator.disconnect()
                except Exception as e:
                    logger.error(f"Error stopping simulator: {e}")
            
            # Close child windows
            logger.debug("Closing child windows")
            for window_name, window in [
                ('connect_form', self.connect_form),
                ('eeg_data_form', self.eeg_data_form),
                ('gyro_form', self.gyro_form),
                ('config_form', self.config_form)
            ]:
                if window:
                    try:
                        window.close()
                    except Exception as e:
                        logger.error(f"Error closing {window_name}: {e}")
            
            # Cleanup tray icon
            logger.info("Cleaning up tray icon")
            try:
                self.tray_icon.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up tray icon: {e}")
            
            logger.info("All resources cleaned up successfully")
            
            # Quit the application
            from PyQt5.QtWidgets import QApplication
            QApplication.quit()
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}", exc_info=True)
            # Quit anyway to allow app to close
            from PyQt5.QtWidgets import QApplication
            QApplication.quit()
