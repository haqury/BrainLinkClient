"""Connection form for discovering and connecting to BrainLink devices"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
    QPushButton, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import asyncio
from typing import List, Tuple

from services.bluetooth_service import BluetoothService
from services.device_simulator import SimulatorController


class DeviceScanner(QThread):
    """Thread for scanning Bluetooth devices"""
    
    devices_found = pyqtSignal(list)
    scan_finished = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.bluetooth_service = BluetoothService()
    
    def run(self):
        """Run device scan in background thread"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            devices = loop.run_until_complete(
                self.bluetooth_service.discover_devices(timeout=10.0)
            )
            self.devices_found.emit(devices)
            loop.close()
        except Exception as e:
            print(f"Scan error: {e}")
        finally:
            self.scan_finished.emit()


class ConnectForm(QDialog):
    """Dialog for connecting to BrainLink devices"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_window = parent
        self.devices: List[Tuple[str, str]] = []
        self.scanner: DeviceScanner = None
        
        self.init_ui()
        self.start_scan()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Connect to BrainLink Device")
        self.setGeometry(200, 200, 400, 350)
        
        layout = QVBoxLayout(self)
        
        # Instructions
        lbl_info = QLabel("Scanning for Bluetooth devices...")
        layout.addWidget(lbl_info)
        
        # Simulator button (for testing without device)
        self.btn_simulator = QPushButton("🎮 Use Simulator (for testing)")
        self.btn_simulator.clicked.connect(self.on_simulator_clicked)
        self.btn_simulator.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        layout.addWidget(self.btn_simulator)
        
        # Device list
        self.device_list = QListWidget()
        layout.addWidget(self.device_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.btn_scan = QPushButton("Rescan")
        self.btn_scan.clicked.connect(self.start_scan)
        self.btn_scan.setEnabled(False)
        button_layout.addWidget(self.btn_scan)
        
        self.btn_connect = QPushButton("Connect")
        self.btn_connect.clicked.connect(self.on_connect_clicked)
        button_layout.addWidget(self.btn_connect)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.close)
        button_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(button_layout)
    
    def start_scan(self):
        """Start scanning for devices"""
        self.device_list.clear()
        self.devices.clear()
        self.btn_scan.setEnabled(False)
        self.btn_connect.setEnabled(False)
        
        # Start scanner thread
        self.scanner = DeviceScanner()
        self.scanner.devices_found.connect(self.on_devices_found)
        self.scanner.scan_finished.connect(self.on_scan_finished)
        self.scanner.start()
    
    def on_devices_found(self, devices: List[Tuple[str, str]]):
        """Handle found devices"""
        self.devices = devices
        
        for address, name in devices:
            display_text = f"{name} - {address}"
            self.device_list.addItem(display_text)
    
    def on_scan_finished(self):
        """Handle scan completion"""
        self.btn_scan.setEnabled(True)
        self.btn_connect.setEnabled(True)
        
        if not self.devices:
            self.device_list.addItem("No devices found. Try rescan.")
    
    def on_connect_clicked(self):
        """Handle connect button click"""
        current_row = self.device_list.currentRow()
        
        if 0 <= current_row < len(self.devices):
            address, name = self.devices[current_row]
            print(f"Connecting to {name} ({address})")
            
            # Notify parent window
            if hasattr(self.parent_window, 'connect_device'):
                self.parent_window.connect_device(address)
            
            self.close()
        else:
            print("Please select a device")
    
    def on_simulator_clicked(self):
        """Handle simulator button click"""
        reply = QMessageBox.question(
            self,
            "Use Simulator",
            "Start device simulator for testing?\n\n"
            "The simulator will generate fake EEG and gyro data.\n"
            "This is useful for testing without a real BrainLink device.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Create and start simulator
            simulator = SimulatorController(self.parent_window)
            simulator.connect()
            
            # Store simulator in parent
            self.parent_window.simulator = simulator
            
            QMessageBox.information(
                self,
                "Simulator Started",
                "✅ Device simulator is now running!\n\n"
                "You should see EEG data updating in the main window.\n"
                "Open 'EEG Data' window to see real-time values."
            )
            
            self.close()
