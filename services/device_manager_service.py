"""Device Manager Service for BrainLink devices"""

import logging
import json
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass
from PyQt5.QtCore import QObject, QThread, pyqtSignal
import asyncio

from pybrainlink import BrainLinkDevice

logger = logging.getLogger(__name__)


@dataclass
class DeviceInfo:
    """Information about a BrainLink device"""
    address: str
    name: str
    is_simulator: bool = False
    
    def __str__(self):
        if self.is_simulator:
            return "🎮 Simulator (for testing)"
        return f"{self.name} - {self.address}"
    
    def to_dict(self):
        return {
            'address': self.address,
            'name': self.name,
            'is_simulator': self.is_simulator
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            address=data.get('address', ''),
            name=data.get('name', ''),
            is_simulator=data.get('is_simulator', False)
        )


class DeviceScannerThread(QThread):
    """Thread for scanning Bluetooth devices"""
    
    devices_found = pyqtSignal(list)  # List[DeviceInfo]
    scan_finished = pyqtSignal()
    scan_error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.device = BrainLinkDevice()
    
    def run(self):
        """Run device scan in background thread"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            devices = loop.run_until_complete(
                self.device.scan(timeout=10.0)
            )
            
            # Convert to DeviceInfo objects
            device_infos = [
                DeviceInfo(address=addr, name=name, is_simulator=False)
                for addr, name in devices
            ]
            
            self.devices_found.emit(device_infos)
            loop.close()
            
        except Exception as e:
            logger.error(f"Scan error: {e}", exc_info=True)
            self.scan_error.emit(str(e))
        finally:
            self.scan_finished.emit()


class DeviceManagerService(QObject):
    """Service for managing BrainLink device connections"""
    
    # Signals
    devices_updated = pyqtSignal(list)  # List[DeviceInfo]
    scan_started = pyqtSignal()
    scan_finished = pyqtSignal()
    
    # Simulator device constant
    SIMULATOR_DEVICE = DeviceInfo(
        address="simulator",
        name="Simulator",
        is_simulator=True
    )
    
    def __init__(self, config_path: str = "config/device_config.json"):
        super().__init__()
        self.config_path = Path(config_path)
        self.devices: List[DeviceInfo] = []
        self.scanner: Optional[DeviceScannerThread] = None
        self.last_device: Optional[DeviceInfo] = None
        
        # Always add simulator as first device
        self.devices.append(self.SIMULATOR_DEVICE)
        
        # Load saved configuration
        self._load_config()
        
        logger.info("DeviceManagerService initialized")
    
    def start_scan(self):
        """Start scanning for Bluetooth devices"""
        logger.info("Starting device scan...")
        
        # Keep simulator, clear other devices
        self.devices = [self.SIMULATOR_DEVICE]
        self.devices_updated.emit(self.devices)
        
        # Start scanner thread
        self.scanner = DeviceScannerThread()
        self.scanner.devices_found.connect(self._on_devices_found)
        self.scanner.scan_finished.connect(self._on_scan_finished)
        self.scanner.scan_error.connect(self._on_scan_error)
        self.scanner.start()
        
        self.scan_started.emit()
    
    def _on_devices_found(self, new_devices: List[DeviceInfo]):
        """Handle found devices"""
        logger.info(f"Found {len(new_devices)} devices")
        
        # Add new devices (simulator is already first)
        self.devices.extend(new_devices)
        self.devices_updated.emit(self.devices)
    
    def _on_scan_finished(self):
        """Handle scan completion"""
        logger.info(f"Scan finished. Total devices: {len(self.devices)}")
        self.scan_finished.emit()
    
    def _on_scan_error(self, error_msg: str):
        """Handle scan error"""
        logger.error(f"Scan error: {error_msg}")
        self.scan_finished.emit()
    
    def get_devices(self) -> List[DeviceInfo]:
        """Get list of available devices"""
        return self.devices.copy()
    
    def get_device_by_address(self, address: str) -> Optional[DeviceInfo]:
        """Get device by address"""
        for device in self.devices:
            if device.address == address:
                return device
        return None
    
    def save_last_device(self, device: DeviceInfo):
        """Save last connected device to config"""
        self.last_device = device
        self._save_config()
        logger.info(f"Saved last device: {device}")
    
    def get_last_device(self) -> Optional[DeviceInfo]:
        """Get last connected device from config"""
        return self.last_device
    
    def stop_scan(self):
        """Stop scanning for devices"""
        if self.scanner and self.scanner.isRunning():
            logger.info("Stopping device scan")
            self.scanner.terminate()
            self.scanner.wait(1000)  # Wait up to 1 second
            if self.scanner.isRunning():
                logger.warning("Force stopping scanner thread")
                self.scanner.terminate()
                self.scanner.wait(500)
            self.scanner = None
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            config = {
                'last_device': self.last_device.to_dict() if self.last_device else None
            }
            
            # Ensure config directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved config to {self.config_path}")
        
        except Exception as e:
            logger.error(f"Error saving config: {e}", exc_info=True)
    
    def _load_config(self):
        """Load configuration from file"""
        try:
            if not self.config_path.exists():
                logger.info("No config file found, using defaults")
                return
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if config.get('last_device'):
                self.last_device = DeviceInfo.from_dict(config['last_device'])
                logger.info(f"Loaded last device: {self.last_device}")
        
        except Exception as e:
            logger.error(f"Error loading config: {e}", exc_info=True)
    
    @staticmethod
    def check_bluetooth_available() -> Tuple[bool, str]:
        """
        Check if Bluetooth is available and enabled
        
        Returns:
            Tuple of (is_available, message)
        """
        try:
            import platform
            system = platform.system()
            
            if system == "Windows":
                # Try to scan briefly to check if BT is available
                try:
                    device = BrainLinkDevice()
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Quick scan to check if BT works
                    loop.run_until_complete(device.scan(timeout=1.0))
                    loop.close()
                    
                    return True, "Bluetooth is available"
                
                except Exception as e:
                    error_msg = str(e).lower()
                    
                    if "bluetooth" in error_msg or "bl" in error_msg:
                        return False, "Bluetooth is not enabled or not available"
                    else:
                        return False, f"Bluetooth error: {e}"
            
            else:
                # For Linux/Mac, assume available (pybrainlink will handle errors)
                return True, "Bluetooth assumed available"
        
        except Exception as e:
            logger.error(f"Error checking Bluetooth: {e}", exc_info=True)
            return False, f"Error checking Bluetooth: {e}"
