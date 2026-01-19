"""Bluetooth service for BrainLink device connection"""

import asyncio
from typing import Optional, Callable, List, Tuple
from bleak import BleakScanner, BleakClient
from .brainlink_protocol_parser import BrainLinkProtocolParser


class BluetoothService:
    """Service for managing Bluetooth connections to BrainLink device"""

    def __init__(self):
        self.client: Optional[BleakClient] = None
        self.is_connected = False
        self.on_device_found: Optional[Callable[[str, str], None]] = None
        self.on_eeg_data: Optional[Callable] = None
        self.on_gyro_data: Optional[Callable] = None
        self.on_hrv_data: Optional[Callable] = None
        self._scanning = False
        self.parser = BrainLinkProtocolParser()

    async def discover_devices(self, timeout: float = 10.0) -> List[Tuple[str, str]]:
        """
        Discover nearby Bluetooth devices
        
        Args:
            timeout: Scan timeout in seconds
            
        Returns:
            List of tuples (address, name)
        """
        devices = []
        try:
            print("Starting Bluetooth scan...")
            discovered = await BleakScanner.discover(timeout=timeout)
            
            for device in discovered:
                if device.name:  # Only include devices with names
                    devices.append((device.address, device.name))
                    print(f"Found device: {device.name} ({device.address})")
                    
                    # Notify callback if set
                    if self.on_device_found:
                        # Convert address to long format similar to C# version
                        self.on_device_found(device.address, device.name)
                        
        except Exception as e:
            print(f"Error during device discovery: {e}")
            
        return devices

    async def connect(self, address: str) -> bool:
        """
        Connect to a Bluetooth device
        
        Args:
            address: Device MAC address or identifier
            
        Returns:
            True if connected successfully
        """
        try:
            print(f"Connecting to {address}...")
            self.client = BleakClient(address)
            await self.client.connect()
            self.is_connected = True
            print(f"Connected to {address}")
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            self.is_connected = False
            return False

    async def disconnect(self):
        """Disconnect from the current device"""
        if self.client and self.is_connected:
            try:
                await self.client.disconnect()
                self.is_connected = False
                print("Disconnected")
            except Exception as e:
                print(f"Disconnect error: {e}")

    async def start_notifications(self, characteristic_uuid: str):
        """
        Start receiving notifications from a characteristic
        
        Args:
            characteristic_uuid: UUID of the characteristic to monitor
        """
        if not self.client or not self.is_connected:
            print("Not connected to device")
            return

        try:
            await self.client.start_notify(
                characteristic_uuid,
                self._notification_handler
            )
            print(f"Started notifications for {characteristic_uuid}")
        except Exception as e:
            print(f"Error starting notifications: {e}")
    
    async def start_all_notifications(self):
        """Discover and start notifications for all available characteristics"""
        if not self.client or not self.is_connected:
            print("Not connected to device")
            return
        
        try:
            print("\n📋 Discovering services and characteristics...")
            services = self.client.services
            
            for service in services:
                print(f"\n🔷 Service: {service.uuid}")
                
                for char in service.characteristics:
                    print(f"  📌 Characteristic: {char.uuid}")
                    print(f"     Properties: {char.properties}")
                    
                    # Start notifications for characteristics that support it
                    if "notify" in char.properties:
                        try:
                            await self.client.start_notify(char.uuid, self._notification_handler)
                            print(f"     ✅ Started notifications")
                        except Exception as e:
                            print(f"     ❌ Failed to start notifications: {e}")
            
            print("\n✅ All notifications started!\n")
            
        except Exception as e:
            print(f"Error discovering characteristics: {e}")

    def _notification_handler(self, sender, data: bytearray):
        """
        Handle incoming notification data
        
        Args:
            sender: Characteristic that sent the data
            data: Raw data bytes
        """
        # Parse data using protocol parser
        eeg_data, gyro_data = self.parser.parse_data(data)
        
        # Call callbacks if data was parsed
        if eeg_data and self.on_eeg_data:
            self.on_eeg_data(eeg_data)
        
        if gyro_data and self.on_gyro_data:
            x, y, z = gyro_data
            self.on_gyro_data(x, y, z)

    def close(self):
        """Close the Bluetooth connection"""
        if self.client:
            asyncio.create_task(self.disconnect())


# Synchronous wrapper for easier use in UI
class BluetoothServiceSync:
    """Synchronous wrapper for BluetoothService"""

    def __init__(self):
        self.service = BluetoothService()
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    def start(self):
        """Start the Bluetooth service"""
        if not self.loop or self.loop.is_closed():
            self.loop = asyncio.new_event_loop()

    def discover_devices_sync(self, timeout: float = 10.0) -> List[Tuple[str, str]]:
        """Synchronous device discovery"""
        if not self.loop:
            self.start()
        return self.loop.run_until_complete(
            self.service.discover_devices(timeout)
        )

    def connect_sync(self, address: str) -> bool:
        """Synchronous connect"""
        if not self.loop:
            self.start()
        return self.loop.run_until_complete(
            self.service.connect(address)
        )

    def close(self):
        """Close the service"""
        self.service.close()
        if self.loop:
            self.loop.close()
