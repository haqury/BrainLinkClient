"""Shared Memory Service for ultra-fast game integration via shared memory"""

import logging
import struct
from multiprocessing import shared_memory, Lock
from typing import Optional, Dict, Any
from dataclasses import dataclass
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

logger = logging.getLogger(__name__)


@dataclass
class SharedMemoryLayout:
    """Layout of shared memory structure (all values as int32)"""
    # Header
    VERSION: int = 0  # offset 0: protocol version
    TIMESTAMP: int = 1  # offset 4: timestamp (ms since start)
    
    # EEG Basic
    ATTENTION: int = 2  # offset 8
    MEDITATION: int = 3  # offset 12
    SIGNAL: int = 4  # offset 16
    
    # EEG Waves
    DELTA: int = 5  # offset 20
    THETA: int = 6  # offset 24
    LOW_ALPHA: int = 7  # offset 28
    HIGH_ALPHA: int = 8  # offset 32
    LOW_BETA: int = 9  # offset 36
    HIGH_BETA: int = 10  # offset 40
    LOW_GAMMA: int = 11  # offset 44
    HIGH_GAMMA: int = 12  # offset 48
    
    # Event (as integer code)
    EVENT_CODE: int = 13  # offset 52: 0=none, 1=ml, 2=mr, 3=mu, 4=md, 5=stop
    
    # Gyro
    GYRO_X: int = 14  # offset 56
    GYRO_Y: int = 15  # offset 60
    GYRO_Z: int = 16  # offset 64
    
    # Extended data
    AP: int = 17  # offset 68
    ELECTRIC: int = 18  # offset 72
    TEMP: int = 19  # offset 76
    HEART: int = 20  # offset 80
    
    # === CLIENT -> SERVER COMMANDS (bidirectional communication) ===
    COMMAND_PENDING: int = 21  # offset 84: 1 if command pending, 0 if processed
    COMMAND_TYPE: int = 22  # offset 88: 1=save_event, 2=save_ml_training
    COMMAND_EVENT_CODE: int = 23  # offset 92: event code to save
    COMMAND_TIMESTAMP: int = 24  # offset 96: client timestamp
    
    # Total size
    TOTAL_FIELDS: int = 25
    TOTAL_SIZE: int = TOTAL_FIELDS * 4  # 100 bytes (25 int32)


# Event name to code mapping
EVENT_TO_CODE = {
    "": 0,
    "ml": 1,  # Move Left
    "mr": 2,  # Move Right
    "mu": 3,  # Move Up
    "md": 4,  # Move Down
    "stop": 5,
}

CODE_TO_EVENT = {v: k for k, v in EVENT_TO_CODE.items()}


class SharedMemoryService(QObject):
    """
    Shared Memory service for ultra-fast game integration.
    
    Provides direct memory access for games to read BrainLink data
    with minimal latency (~0.01-0.05ms).
    
    Features:
    - 0.01-0.05ms latency (fastest possible)
    - No serialization overhead
    - Direct memory access
    - Thread-safe with locks
    - Fixed memory layout for easy reading
    """
    
    # Signals
    service_started = pyqtSignal(str)  # memory name
    service_stopped = pyqtSignal()
    error_occurred = pyqtSignal(str)
    command_received = pyqtSignal(dict)  # command from client
    
    # Memory name constant
    MEMORY_NAME = "brainlink_data"
    
    def __init__(self):
        super().__init__()
        
        self.shm: Optional[shared_memory.SharedMemory] = None
        self.lock: Optional[Lock] = None
        self.is_running = False
        self.layout = SharedMemoryLayout()
        self.start_time = 0
        
        # Timer for checking commands from clients
        self.command_timer = QTimer()
        self.command_timer.timeout.connect(self._check_commands)
        
        # Statistics
        self.updates_sent = 0
        self.commands_received = 0
        
        logger.info("SharedMemoryService initialized")
    
    def start(self):
        """Start the shared memory service"""
        if self.is_running:
            logger.warning("Shared memory service already running")
            return
        
        try:
            import time
            self.start_time = int(time.time() * 1000)
            
            # Try to unlink existing memory (cleanup from previous crash)
            try:
                existing = shared_memory.SharedMemory(name=self.MEMORY_NAME)
                existing.close()
                existing.unlink()
                logger.info("Cleaned up existing shared memory")
            except FileNotFoundError:
                pass  # No existing memory, that's fine
            
            # Create shared memory
            self.shm = shared_memory.SharedMemory(
                name=self.MEMORY_NAME,
                create=True,
                size=self.layout.TOTAL_SIZE
            )
            
            # Create lock for thread-safe access
            self.lock = Lock()
            
            # Initialize memory with zeros
            with self.lock:
                # Write version number
                self._write_int(self.layout.VERSION, 1)
                # Zero out all other fields
                for i in range(1, self.layout.TOTAL_FIELDS):
                    self._write_int(i, 0)
            
            self.is_running = True
            
            # Start command polling timer (check every 10ms for client commands)
            self.command_timer.start(10)
            
            self.service_started.emit(self.MEMORY_NAME)
            logger.info(f"Shared memory service started: {self.MEMORY_NAME}")
            logger.info(f"Memory size: {self.layout.TOTAL_SIZE} bytes")
            logger.info("Command polling started (bidirectional mode)")
            
        except Exception as e:
            logger.error(f"Failed to start shared memory service: {e}", exc_info=True)
            self.error_occurred.emit(f"Failed to start: {e}")
            self.is_running = False
    
    def stop(self):
        """Stop the shared memory service"""
        if not self.is_running:
            logger.warning("Shared memory service not running")
            return
        
        try:
            # Stop command timer
            self.command_timer.stop()
            
            if self.shm:
                self.shm.close()
                self.shm.unlink()
                self.shm = None
            
            self.lock = None
            self.is_running = False
            self.service_stopped.emit()
            logger.info("Shared memory service stopped")
        
        except Exception as e:
            logger.error(f"Error stopping shared memory service: {e}", exc_info=True)
            self.error_occurred.emit(f"Failed to stop: {e}")
    
    def _write_int(self, offset: int, value: int):
        """Write int32 value to shared memory (must be called within lock!)"""
        if not self.shm:
            return
        
        byte_offset = offset * 4
        self.shm.buf[byte_offset:byte_offset + 4] = struct.pack('i', value)
    
    def _update_timestamp(self):
        """Update timestamp in shared memory"""
        import time
        current_time = int(time.time() * 1000)
        timestamp = current_time - self.start_time
        self._write_int(self.layout.TIMESTAMP, timestamp)
    
    def update_eeg_data(self, data: Dict[str, Any]):
        """
        Update EEG data in shared memory
        
        Args:
            data: Dictionary with EEG data and event
        """
        if not self.is_running or not self.shm or not self.lock:
            return
        
        try:
            with self.lock:
                # Update timestamp
                self._update_timestamp()
                
                # Basic EEG
                self._write_int(self.layout.ATTENTION, data.get("attention", 0))
                self._write_int(self.layout.MEDITATION, data.get("meditation", 0))
                self._write_int(self.layout.SIGNAL, data.get("signal", 0))
                
                # Waves
                self._write_int(self.layout.DELTA, data.get("delta", 0))
                self._write_int(self.layout.THETA, data.get("theta", 0))
                self._write_int(self.layout.LOW_ALPHA, data.get("low_alpha", 0))
                self._write_int(self.layout.HIGH_ALPHA, data.get("high_alpha", 0))
                self._write_int(self.layout.LOW_BETA, data.get("low_beta", 0))
                self._write_int(self.layout.HIGH_BETA, data.get("high_beta", 0))
                self._write_int(self.layout.LOW_GAMMA, data.get("low_gamma", 0))
                self._write_int(self.layout.HIGH_GAMMA, data.get("high_gamma", 0))
                
                # Event (convert string to code)
                event_name = data.get("event", "")
                event_code = EVENT_TO_CODE.get(event_name, 0)
                self._write_int(self.layout.EVENT_CODE, event_code)
                
                self.updates_sent += 1
        
        except Exception as e:
            logger.error(f"Error updating EEG data: {e}", exc_info=True)
    
    def update_gyro_data(self, x: int, y: int, z: int):
        """
        Update gyro data in shared memory
        
        Args:
            x, y, z: Gyro coordinates
        """
        if not self.is_running or not self.shm or not self.lock:
            return
        
        try:
            with self.lock:
                self._write_int(self.layout.GYRO_X, x)
                self._write_int(self.layout.GYRO_Y, y)
                self._write_int(self.layout.GYRO_Z, z)
        
        except Exception as e:
            logger.error(f"Error updating gyro data: {e}", exc_info=True)
    
    def update_extended_data(self, ap: int, electric: int, temp: int, heart: int):
        """
        Update extended data in shared memory
        
        Args:
            ap, electric, temp, heart: Extended data values
        """
        if not self.is_running or not self.shm or not self.lock:
            return
        
        try:
            with self.lock:
                self._write_int(self.layout.AP, ap)
                self._write_int(self.layout.ELECTRIC, electric)
                self._write_int(self.layout.TEMP, temp)
                self._write_int(self.layout.HEART, heart)
        
        except Exception as e:
            logger.error(f"Error updating extended data: {e}", exc_info=True)
    
    def _check_commands(self):
        """Check for incoming commands from clients (called by timer)"""
        if not self.is_running or not self.shm or not self.lock:
            return
        
        try:
            with self.lock:
                # Check if command is pending
                command_pending = self._read_int(self.layout.COMMAND_PENDING)
                
                if command_pending == 1:
                    # Read command data
                    command_type = self._read_int(self.layout.COMMAND_TYPE)
                    event_code = self._read_int(self.layout.COMMAND_EVENT_CODE)
                    timestamp = self._read_int(self.layout.COMMAND_TIMESTAMP)
                    
                    # Convert event code to name
                    event_name = CODE_TO_EVENT.get(event_code, "")
                    
                    # Create command dict
                    command = {
                        "type": command_type,  # 1=save_event, 2=save_ml_training
                        "event": event_name,
                        "event_code": event_code,
                        "timestamp": timestamp
                    }
                    
                    # Clear pending flag (acknowledge)
                    self._write_int(self.layout.COMMAND_PENDING, 0)
                    
                    # Emit signal
                    self.commands_received += 1
                    self.command_received.emit(command)
                    logger.info(f"Command received: type={command_type}, event={event_name}")
        
        except Exception as e:
            logger.error(f"Error checking commands: {e}", exc_info=True)
    
    def _read_int(self, offset: int) -> int:
        """Read int32 value from shared memory (must be called within lock!)"""
        if not self.shm:
            return 0
        
        byte_offset = offset * 4
        value = struct.unpack('i', self.shm.buf[byte_offset:byte_offset + 4])[0]
        return value
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            "is_running": self.is_running,
            "memory_name": self.MEMORY_NAME,
            "memory_size": self.layout.TOTAL_SIZE,
            "updates_sent": self.updates_sent,
            "commands_received": self.commands_received,
            "latency": "~0.01-0.05ms",
        }
