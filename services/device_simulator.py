"""Device simulator for testing without real BrainLink device"""

import random
import time
from typing import Optional, Callable
from threading import Thread, Event

from pybrainlink import BrainLinkModel, BrainLinkExtendModel  # Using pybrainlink library


class DeviceSimulator:
    """Simulates BrainLink device for testing"""
    
    def __init__(self):
        self.is_running = False
        self._stop_event = Event()
        self._thread: Optional[Thread] = None
        
        # Callbacks
        self.on_eeg_data: Optional[Callable] = None
        self.on_extend_data: Optional[Callable] = None
        self.on_gyro_data: Optional[Callable] = None
        
        # Simulation parameters
        self.update_interval = 0.1  # 10 Hz
        
    def start(self):
        """Start device simulation"""
        if self.is_running:
            return
            
        self.is_running = True
        self._stop_event.clear()
        self._thread = Thread(target=self._simulation_loop, daemon=True)
        self._thread.start()
        print("Device simulator started")
        
    def stop(self):
        """Stop device simulation"""
        if not self.is_running:
            return
            
        self.is_running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1.0)
        print("Device simulator stopped")
        
    def _simulation_loop(self):
        """Main simulation loop"""
        counter = 0
        
        while not self._stop_event.is_set():
            # Generate EEG data
            if self.on_eeg_data:
                eeg_data = self._generate_eeg_data(counter)
                self.on_eeg_data(eeg_data)
            
            # Generate extended data every second
            if counter % 10 == 0 and self.on_extend_data:
                extend_data = self._generate_extend_data()
                self.on_extend_data(extend_data)
            
            # Generate gyro data
            if self.on_gyro_data:
                x, y, z = self._generate_gyro_data(counter)
                self.on_gyro_data(x, y, z)
            
            counter += 1
            time.sleep(self.update_interval)
    
    def _generate_eeg_data(self, counter: int) -> BrainLinkModel:
        """Generate realistic EEG data"""
        # Base values with some variation
        base_attention = 60
        base_meditation = 50
        
        # Add smooth wave-like variation
        wave = counter * 0.1
        
        return BrainLinkModel(
            attention=int(base_attention + 20 * random.random() + 10 * (wave % 10) / 10),
            meditation=int(base_meditation + 20 * random.random() + 10 * ((wave + 5) % 10) / 10),
            signal=random.randint(0, 100),
            delta=random.randint(80000, 150000),
            theta=random.randint(60000, 100000),
            low_alpha=random.randint(30000, 60000),
            high_alpha=random.randint(20000, 50000),
            low_beta=random.randint(15000, 35000),
            high_beta=random.randint(10000, 25000),
            low_gamma=random.randint(8000, 18000),
            high_gamma=random.randint(5000, 15000)
        )
    
    def _generate_extend_data(self) -> BrainLinkExtendModel:
        """Generate extended device data"""
        return BrainLinkExtendModel(
            ap=random.randint(80, 100),
            electric=random.randint(3500, 4200),
            version="1.0.0",
            temperature=random.uniform(35.0, 37.0),
            heart_rate=random.randint(60, 80)
        )
    
    def _generate_gyro_data(self, counter: int) -> tuple:
        """Generate gyroscope data"""
        # Simulate small head movements
        base_x = 0
        base_y = 0
        base_z = 0
        
        # Add some movement variation
        x = base_x + random.randint(-1000, 1000)
        y = base_y + random.randint(-1000, 1000)
        z = base_z + random.randint(-1000, 1000)
        
        return x, y, z


class SimulatorController:
    """Controller for managing device simulator"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.simulator = DeviceSimulator()
        self.is_connected = False
        
    def connect(self):
        """Connect to simulator"""
        if self.is_connected:
            return
            
        # Set up callbacks
        self.simulator.on_eeg_data = self.main_window.on_eeg_data_event
        self.simulator.on_extend_data = self.main_window.on_extend_data_event
        
        if self.main_window.gyro_form:
            self.simulator.on_gyro_data = self.main_window.gyro_form.update_gyro_data
        
        # Start simulator
        self.simulator.start()
        self.is_connected = True
        print("✅ Simulator connected!")
        
    def disconnect(self):
        """Disconnect from simulator"""
        if not self.is_connected:
            return
            
        self.simulator.stop()
        self.is_connected = False
        print("Simulator disconnected")
