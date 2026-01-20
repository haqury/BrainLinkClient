"""Wrapper for BrainLink SDK DLL integration"""

import sys
import os
from typing import Optional, Callable

HAS_PYTHONNET = False
try:
    import clr
    HAS_PYTHONNET = True
except Exception as e:
    # pythonnet not available or failed to initialize
    # This is OK - we'll use direct Bluetooth parsing instead
    pass

from pybrainlink import BrainLinkModel, BrainLinkExtendModel  # Using pybrainlink library


class BrainLinkSDKWrapper:
    """Wrapper for BrainLinkSDK_Windows.dll"""
    
    def __init__(self, dll_path: Optional[str] = None):
        self.sdk = None
        self.is_initialized = False
        
        # Callbacks
        self.on_eeg_data: Optional[Callable] = None
        self.on_extend_data: Optional[Callable] = None
        self.on_gyro_data: Optional[Callable] = None
        self.on_hrv_data: Optional[Callable] = None
        self.on_raw_data: Optional[Callable] = None
        self.on_device_found: Optional[Callable] = None
        
        # Try to load DLL
        if dll_path:
            self.load_dll(dll_path)
        else:
            # Try default paths
            self.try_load_from_default_paths()
    
    def try_load_from_default_paths(self):
        """Try to load DLL from common locations"""
        possible_paths = [
            # Path from C# project
            r"C:\Users\haqury\source\repos\BrainLinkConnect\bin\Release\BrainLinkSDK_Windows.dll",
            r"C:\Users\haqury\source\repos\BrainLinkConnect\bin\Debug\BrainLinkSDK_Windows.dll",
            # Local path
            os.path.join(os.path.dirname(__file__), "BrainLinkSDK_Windows.dll"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                print(f"Found DLL at: {path}")
                if self.load_dll(path):
                    return True
        
        print("⚠️ BrainLinkSDK_Windows.dll not found in default locations")
        print("Please provide path to DLL or copy it to project directory")
        return False
    
    def load_dll(self, dll_path: str) -> bool:
        """Load BrainLinkSDK DLL"""
        if not HAS_PYTHONNET:
            print("❌ Cannot load DLL: pythonnet not installed")
            print("Install it with: pip install pythonnet")
            return False
        
        if not os.path.exists(dll_path):
            print(f"❌ DLL not found: {dll_path}")
            return False
        
        try:
            # Add DLL directory to path
            dll_dir = os.path.dirname(dll_path)
            if dll_dir not in sys.path:
                sys.path.append(dll_dir)
            
            # Load DLL
            clr.AddReference(dll_path)
            
            # Import BrainLinkSDK namespace
            from BrainLinkSDK_Windows import BrainLinkSDK
            
            # Create SDK instance
            self.sdk = BrainLinkSDK()
            
            # Set up event handlers
            self._setup_event_handlers()
            
            self.is_initialized = True
            print(f"✅ BrainLink SDK loaded successfully from: {dll_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error loading DLL: {e}")
            return False
    
    def _setup_event_handlers(self):
        """Setup event handlers for SDK"""
        if not self.sdk:
            return
        
        # EEG Data Event
        def on_eeg_event(model):
            if self.on_eeg_data:
                # Convert C# model to Python model
                py_model = BrainLinkModel(
                    attention=model.Attention,
                    meditation=model.Meditation,
                    signal=model.Signal,
                    delta=model.Delta,
                    theta=model.Theta,
                    low_alpha=model.LowAlpha,
                    high_alpha=model.HighAlpha,
                    low_beta=model.LowBeta,
                    high_beta=model.HighBeta,
                    low_gamma=model.LowGamma,
                    high_gamma=model.HighGamma
                )
                self.on_eeg_data(py_model)
        
        # Extended Data Event
        def on_extend_event(model):
            if self.on_extend_data:
                py_model = BrainLinkExtendModel(
                    ap=model.Ap,
                    electric=model.Electric,
                    version=str(model.Version),
                    temperature=float(model.Temperature),
                    heart_rate=model.HeartRate
                )
                self.on_extend_data(py_model)
        
        # Gyro Data Event
        def on_gyro_event(x, y, z):
            if self.on_gyro_data:
                self.on_gyro_data(x, y, z)
        
        # Device Found Event
        def on_device_found_event(address, name):
            if self.on_device_found:
                self.on_device_found(address, name)
        
        # Attach events
        try:
            from BrainLinkSDK_Windows import (
                BrainLinkSDKEEGDataEvent,
                BrainLinkSDKEEGExtendDataEvent,
                BrainLinkSDKGyroDataEvent,
                BrainLinkSDKOnDeviceFoundEvent
            )
            
            self.sdk.OnEEGDataEvent += BrainLinkSDKEEGDataEvent(on_eeg_event)
            self.sdk.OnEEGExtendEvent += BrainLinkSDKEEGExtendDataEvent(on_extend_event)
            self.sdk.OnGyroDataEvent += BrainLinkSDKGyroDataEvent(on_gyro_event)
            self.sdk.OnDeviceFound = BrainLinkSDKOnDeviceFoundEvent(on_device_found_event)
            
            print("✅ Event handlers attached")
        except Exception as e:
            print(f"⚠️ Error attaching event handlers: {e}")
    
    def start(self):
        """Start BrainLink SDK"""
        if not self.is_initialized:
            print("❌ SDK not initialized")
            return False
        
        try:
            self.sdk.Start()
            print("✅ BrainLink SDK started")
            return True
        except Exception as e:
            print(f"❌ Error starting SDK: {e}")
            return False
    
    def connect(self, address: int):
        """Connect to device by address"""
        if not self.is_initialized:
            print("❌ SDK not initialized")
            return False
        
        try:
            self.sdk.connect(address)
            print(f"✅ Connecting to device: {address}")
            return True
        except Exception as e:
            print(f"❌ Error connecting: {e}")
            return False
    
    def set_ap_enable(self, enable: bool):
        """Enable/disable AP"""
        if self.is_initialized and self.sdk:
            self.sdk.SetApEnable(enable)
    
    def set_gyro_enable(self, enable: bool):
        """Enable/disable gyroscope"""
        if self.is_initialized and self.sdk:
            self.sdk.SetGyroEnable(enable)
    
    def close(self):
        """Close SDK connection"""
        if self.is_initialized and self.sdk:
            try:
                self.sdk.Close()
                print("✅ BrainLink SDK closed")
            except:
                pass
