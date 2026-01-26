"""
Test script to verify game control is working correctly
Checks if events are being sent to shared memory properly
"""

import time
from multiprocessing import shared_memory
import struct

# Event codes (must match BrainLink Client)
CODE_TO_EVENT = {
    0: "",
    1: "ml",    # Move Left
    2: "mr",    # Move Right
    3: "mu",    # Move Up
    4: "md",    # Move Down
    5: "stop",  # Stop
}

EVENT_CODE_OFFSET = 13  # Must match SharedMemoryLayout.EVENT_CODE

def test_shared_memory():
    """Test reading events from shared memory"""
    memory_name = "brainlink_data"
    
    print("=" * 60)
    print("🧪 Testing Game Control via Shared Memory")
    print("=" * 60)
    print(f"\n📡 Connecting to shared memory: '{memory_name}'")
    
    try:
        shm = shared_memory.SharedMemory(name=memory_name)
        print("✅ Connected to shared memory!")
        
        print("\n📊 Reading events (press Ctrl+C to stop)...")
        print("   Make sure BrainLink Client is running with:")
        print("   - ✅ Enable Shared Memory (checked)")
        print("   - ✅ Enable Game Control (checked)")
        print("   - ✅ Device connected")
        print("   - ✅ Events being detected (checkboxes or ML prediction)\n")
        
        last_event_code = -1
        event_count = {}
        
        for i in range(1000):  # Test for ~100 seconds at 10Hz
            try:
                # Read event code
                byte_offset = EVENT_CODE_OFFSET * 4
                event_code = struct.unpack('i', shm.buf[byte_offset:byte_offset + 4])[0]
                
                # Read other useful data
                attention_offset = 2 * 4
                attention = struct.unpack('i', shm.buf[attention_offset:attention_offset + 4])[0]
                
                timestamp_offset = 1 * 4
                timestamp = struct.unpack('i', shm.buf[timestamp_offset:timestamp_offset + 4])[0]
                
                event_name = CODE_TO_EVENT.get(event_code, f"unknown({event_code})")
                
                # Count events
                if event_name:
                    event_count[event_name] = event_count.get(event_name, 0) + 1
                
                # Print when event changes
                if event_code != last_event_code:
                    if event_code != 0:  # Don't print empty events
                        print(f"🎮 Event: {event_name} (code: {event_code}) | Attention: {attention} | Timestamp: {timestamp}ms")
                    last_event_code = event_code
                
                time.sleep(0.1)  # Check every 100ms
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error reading: {e}")
                time.sleep(0.1)
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 Event Summary:")
        print("=" * 60)
        if event_count:
            for event, count in sorted(event_count.items()):
                print(f"   {event}: {count} times")
        else:
            print("   ⚠️  No events detected!")
            print("\n   Troubleshooting:")
            print("   1. Check that 'Enable Shared Memory' is checked in BrainLink Client")
            print("   2. Check that 'Enable Game Control' is checked")
            print("   3. Make sure device is connected and sending data")
            print("   4. Try selecting events manually (checkboxes) or enable ML prediction")
        
        shm.close()
        print("\n✅ Test completed")
        
    except FileNotFoundError:
        print("❌ Shared memory not found!")
        print("\n   Make sure BrainLink Client is running with Shared Memory enabled.")
        print("   Check the 'Enable Shared Memory' checkbox in BrainLink Client.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_shared_memory()
