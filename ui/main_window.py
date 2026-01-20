"""Main window for BrainLink Client application"""

import logging
import asyncio
import threading
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QCheckBox, QLineEdit, QFileDialog, QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from pynput import keyboard
from typing import Optional

# Using pybrainlink library for BrainLink device models
from pybrainlink import BrainLinkModel, BrainLinkExtendModel
from models.eeg_models import EegHistoryModel, ConfigParams, EegFaultModel
from config_defaults import get_default_config, DEFAULT_HISTORY_PATH
from services.history_service import HistoryService
from services.mouse_service import MouseService
from services.head_tracker_service import HeadTracker
from services.system_service import SystemService
from .styles import apply_brainlink_style

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
        
        # Configuration - load defaults from config_defaults.py
        self.config = get_default_config()
        
        # Child windows
        self.connect_form = None
        self.eeg_data_form = None
        self.gyro_form = None
        self.config_form = None
        
        # Simulator
        self.simulator = None
        
        # State
        self.current_event = ""
        self.keyboard_listener: Optional[keyboard.Listener] = None
        
        # Connection management
        self._connection_thread: Optional[threading.Thread] = None
        self._connection_loop: Optional[asyncio.AbstractEventLoop] = None
        self._is_connected = False
        
        # Setup UI
        self.init_ui()
        self.setup_keyboard_listener()
        
        # Connect signals
        self.eeg_data_updated.connect(self.on_eeg_data_updated)
        self.extend_data_updated.connect(self.on_extend_data_updated)
        self.connection_error.connect(self.on_connection_error)
        self.connection_success.connect(self.on_connection_success)
        
        logger.info("MainWindow initialized")

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
        
        self.btn_start = QPushButton("Start & Connect")
        self.btn_start.clicked.connect(self.on_start_clicked)
        connection_layout.addWidget(self.btn_start)
        
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
        
        control_layout.addWidget(self.cb_autouse)
        control_layout.addWidget(self.cb_use_key)
        
        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)
        
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

    def on_start_clicked(self):
        """Handle start button click - open device connection dialog"""
        from ui.connect_form import ConnectForm
        self.connect_form = ConnectForm(self)
        self.connect_form.show()

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

    def update_counter(self):
        """Update history counter display"""
        self.lbl_counter.setText(str(self.history_service.count()))

    def get_event_name(self) -> str:
        """Get currently selected event name"""
        if self.cb_ml.isChecked():
            return "ml"
        elif self.cb_mr.isChecked():
            return "mr"
        elif self.cb_mu.isChecked():
            return "mu"
        elif self.cb_md.isChecked():
            return "md"
        elif self.cb_stop.isChecked():
            return "stop"
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
                
                # Connect to gyro if form exists
                if self.gyro_form:
                    device.on_gyro_data = self.gyro_form.update_gyro_data
                
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
        logger.info("Device disconnected")
    
    def on_connection_error(self, error_msg: str):
        """Handle connection error signal (called in main thread)"""
        logger.error(f"Connection error in UI: {error_msg}")
        QMessageBox.critical(
            self,
            "Connection Error",
            f"Failed to connect to device:\n\n{error_msg}\n\nCheck logs for details."
        )
    
    def on_connection_success(self, address: str):
        """Handle successful connection signal (called in main thread)"""
        logger.info(f"Connection successful in UI: {address}")
        QMessageBox.information(
            self,
            "Connected",
            f"Successfully connected to device:\n{address}"
        )
    
    def on_eeg_data_event(self, model: BrainLinkModel):
        """Handle EEG data event (called from device)"""
        self.eeg_data_updated.emit(model)

    def on_eeg_data_updated(self, model: BrainLinkModel):
        """Handle EEG data in main thread"""
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
            event_name=self.get_event_name()
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
            self.update_counter()

    def on_extend_data_event(self, model: BrainLinkExtendModel):
        """Handle extended data event (called from device)"""
        self.extend_data_updated.emit(model)

    def on_extend_data_updated(self, model: BrainLinkExtendModel):
        """Handle extended data in main thread"""
        self.lbl_ap.setText(str(model.ap))
        self.lbl_electric.setText(str(model.electric))
        self.lbl_version.setText(model.version)
        self.lbl_temp.setText(str(model.temperature))
        self.lbl_heart.setText(str(model.heart_rate))

    def closeEvent(self, event):
        """Handle window close event with proper resource cleanup"""
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
            
            logger.info("All resources cleaned up successfully")
            event.accept()
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}", exc_info=True)
            # Accept anyway to allow app to close
            event.accept()
