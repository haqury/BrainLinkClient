"""
Simple Shared Memory Client for reading BrainLink data

This is the FASTEST way to get BrainLink data in your Python game!
Latency: ~0.01-0.05ms (100x faster than WebSocket!)
"""

from multiprocessing import shared_memory
import struct
import time


# Event code to name mapping
CODE_TO_EVENT = {
    0: "",
    1: "ml",    # Move Left
    2: "mr",    # Move Right
    3: "mu",    # Move Up
    4: "md",    # Move Down
    5: "stop",  # Stop
}


class BrainLinkSharedMemoryClient:
    """Ultra-fast client for reading BrainLink data from shared memory"""
    
    # Memory layout (same as in services/shared_memory_service.py)
    VERSION = 0
    TIMESTAMP = 1
    ATTENTION = 2
    MEDITATION = 3
    SIGNAL = 4
    DELTA = 5
    THETA = 6
    LOW_ALPHA = 7
    HIGH_ALPHA = 8
    LOW_BETA = 9
    HIGH_BETA = 10
    LOW_GAMMA = 11
    HIGH_GAMMA = 12
    EVENT_CODE = 13
    GYRO_X = 14
    GYRO_Y = 15
    GYRO_Z = 16
    AP = 17
    ELECTRIC = 18
    TEMP = 19
    HEART = 20
    
    # Command fields (for sending events back to BrainLink)
    COMMAND_PENDING = 21
    COMMAND_TYPE = 22
    COMMAND_EVENT_CODE = 23
    COMMAND_TIMESTAMP = 24
    
    TOTAL_SIZE = 25 * 4  # 25 fields * 4 bytes (int32)
    
    def __init__(self, memory_name="brainlink_data"):
        """
        Initialize client
        
        Args:
            memory_name: Name of shared memory (must match server)
        """
        self.memory_name = memory_name
        self.shm = None
        self.connected = False
    
    def connect(self):
        """Connect to shared memory"""
        try:
            self.shm = shared_memory.SharedMemory(name=self.memory_name)
            self.connected = True
            print(f"✅ Connected to BrainLink shared memory: '{self.memory_name}'")
            print(f"   Memory size: {self.TOTAL_SIZE} bytes")
            print(f"   Latency: ~0.01-0.05ms (ultra-fast!)")
            return True
        
        except FileNotFoundError:
            print(f"❌ Shared memory '{self.memory_name}' not found!")
            print("   Make sure BrainLink Client is running with Shared Memory enabled.")
            self.connected = False
            return False
        
        except Exception as e:
            print(f"❌ Error connecting to shared memory: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from shared memory"""
        if self.shm:
            self.shm.close()
            self.shm = None
        self.connected = False
        print("🛑 Disconnected from shared memory")
    
    def _read_int(self, offset: int) -> int:
        """Read int32 value from shared memory"""
        if not self.shm:
            return 0
        
        byte_offset = offset * 4
        value = struct.unpack('i', self.shm.buf[byte_offset:byte_offset + 4])[0]
        return value
    
    def _write_int(self, offset: int, value: int):
        """Write int32 value to shared memory"""
        if not self.shm:
            return
        
        byte_offset = offset * 4
        self.shm.buf[byte_offset:byte_offset + 4] = struct.pack('i', value)
    
    def get_all_data(self) -> dict:
        """
        Read all data from shared memory
        
        Returns:
            Dictionary with all BrainLink data
        """
        if not self.connected:
            return {}
        
        # Read all fields
        data = {
            "version": self._read_int(self.VERSION),
            "timestamp": self._read_int(self.TIMESTAMP),
            "attention": self._read_int(self.ATTENTION),
            "meditation": self._read_int(self.MEDITATION),
            "signal": self._read_int(self.SIGNAL),
            "delta": self._read_int(self.DELTA),
            "theta": self._read_int(self.THETA),
            "low_alpha": self._read_int(self.LOW_ALPHA),
            "high_alpha": self._read_int(self.HIGH_ALPHA),
            "low_beta": self._read_int(self.LOW_BETA),
            "high_beta": self._read_int(self.HIGH_BETA),
            "low_gamma": self._read_int(self.LOW_GAMMA),
            "high_gamma": self._read_int(self.HIGH_GAMMA),
            "event_code": self._read_int(self.EVENT_CODE),
            "gyro_x": self._read_int(self.GYRO_X),
            "gyro_y": self._read_int(self.GYRO_Y),
            "gyro_z": self._read_int(self.GYRO_Z),
            "ap": self._read_int(self.AP),
            "electric": self._read_int(self.ELECTRIC),
            "temp": self._read_int(self.TEMP),
            "heart": self._read_int(self.HEART),
        }
        
        # Convert event code to name
        data["event"] = CODE_TO_EVENT.get(data["event_code"], "")
        
        return data
    
    def get_event(self) -> str:
        """Get current event (fastest method - reads only 1 field!)"""
        if not self.connected:
            return ""
        
        event_code = self._read_int(self.EVENT_CODE)
        return CODE_TO_EVENT.get(event_code, "")
    
    def get_attention(self) -> int:
        """Get attention level"""
        return self._read_int(self.ATTENTION) if self.connected else 0
    
    def get_meditation(self) -> int:
        """Get meditation level"""
        return self._read_int(self.MEDITATION) if self.connected else 0
    
    def get_gyro(self) -> tuple:
        """Get gyro data (x, y, z)"""
        if not self.connected:
            return (0, 0, 0)
        
        return (
            self._read_int(self.GYRO_X),
            self._read_int(self.GYRO_Y),
            self._read_int(self.GYRO_Z)
        )
    
    def send_event_to_history(self, event_name: str) -> bool:
        """
        Send event to BrainLink Client to save in history
        
        Args:
            event_name: Event name ("ml", "mr", "mu", "md", "stop", or custom)
        
        Returns:
            True if command sent successfully
        """
        if not self.connected:
            print("❌ Not connected to shared memory")
            return False
        
        try:
            import time
            
            # Convert event name to code (or use 0 for custom events)
            event_codes = {"ml": 1, "mr": 2, "mu": 3, "md": 4, "stop": 5}
            event_code = event_codes.get(event_name, 0)
            
            # Write command
            self._write_int(self.COMMAND_TYPE, 1)  # 1 = save to history
            self._write_int(self.COMMAND_EVENT_CODE, event_code)
            self._write_int(self.COMMAND_TIMESTAMP, int(time.time() * 1000))
            self._write_int(self.COMMAND_PENDING, 1)  # Set pending flag last
            
            print(f"📤 Sent event to history: {event_name}")
            return True
        
        except Exception as e:
            print(f"❌ Error sending event: {e}")
            return False
    
    def send_event_for_ml_training(self, event_name: str) -> bool:
        """
        Send event to BrainLink Client for ML training
        
        Args:
            event_name: Event name ("ml", "mr", "mu", "md", "stop")
        
        Returns:
            True if command sent successfully
        """
        if not self.connected:
            print("❌ Not connected to shared memory")
            return False
        
        try:
            import time
            
            # Convert event name to code
            event_codes = {"ml": 1, "mr": 2, "mu": 3, "md": 4, "stop": 5}
            event_code = event_codes.get(event_name, 0)
            
            if event_code == 0:
                print(f"⚠️ Invalid event name for ML: {event_name}")
                return False
            
            # Write command
            self._write_int(self.COMMAND_TYPE, 2)  # 2 = save for ML training
            self._write_int(self.COMMAND_EVENT_CODE, event_code)
            self._write_int(self.COMMAND_TIMESTAMP, int(time.time() * 1000))
            self._write_int(self.COMMAND_PENDING, 1)  # Set pending flag last
            
            print(f"📤 Sent ML training sample: {event_name}")
            return True
        
        except Exception as e:
            print(f"❌ Error sending ML training data: {e}")
            return False


# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    print("=" * 60)
    print("BrainLink Shared Memory Client - Simple Example")
    print("=" * 60)
    print()
    
    # Create client
    client = BrainLinkSharedMemoryClient()
    
    # Connect
    if not client.connect():
        print("\nMake sure:")
        print("  1. BrainLink Client is running")
        print("  2. Shared Memory is enabled (checkbox in UI)")
        exit(1)
    
    print()
    print("Reading BrainLink data...")
    print("Press Ctrl+C to exit")
    print("-" * 60)
    
    try:
        last_event = ""
        
        while True:
            # Read all data
            data = client.get_all_data()
            
            # Display event if changed
            current_event = data.get("event", "")
            if current_event and current_event != last_event:
                print(f"\n🎯 EVENT: {current_event}")
                print(f"   Attention: {data['attention']}")
                print(f"   Meditation: {data['meditation']}")
                print("-" * 60)
                last_event = current_event
            
            # Small sleep to avoid 100% CPU (optional)
            time.sleep(0.01)  # 10ms = 100 updates/sec
    
    except KeyboardInterrupt:
        print("\n\n🛑 Stopped by user")
    
    finally:
        client.disconnect()
        print("👋 Goodbye!")
