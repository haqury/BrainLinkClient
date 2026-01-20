"""
Bidirectional Shared Memory Example

This example shows how to:
1. READ events from BrainLink (Game receives player thoughts)
2. SEND events back to BrainLink (Game saves events to history/ML)

Perfect for games that want to record player actions for training!
"""

import time
from shared_memory_client import BrainLinkSharedMemoryClient


def simple_example():
    """Simple example: Read events and save them to history"""
    print("=" * 60)
    print("📡 Bidirectional Shared Memory - Simple Example")
    print("=" * 60)
    print("\nThis example shows:")
    print("  1. Reading events from BrainLink")
    print("  2. Sending events back to save in history")
    print()
    
    # Connect
    client = BrainLinkSharedMemoryClient()
    if not client.connect():
        print("\n❌ Failed to connect!")
        return
    
    print("\n🎮 Game started!")
    print("Think events (ml, mr, mu, md, stop) - they will be saved to history")
    print("Press Ctrl+C to exit")
    print("-" * 60)
    
    last_event = ""
    event_count = 0
    
    try:
        while True:
            # Read current event
            event = client.get_event()
            
            # If event changed and not empty
            if event and event != last_event:
                print(f"\n🎯 Event detected: {event}")
                
                # Send event back to BrainLink to save in history
                if client.send_event_to_history(event):
                    event_count += 1
                    print(f"   ✅ Saved to history (total: {event_count})")
                
                last_event = event
            
            time.sleep(0.01)  # 100 FPS polling
    
    except KeyboardInterrupt:
        print("\n\n🛑 Stopped by user")
    
    finally:
        client.disconnect()
        print(f"📊 Total events saved: {event_count}")
        print("👋 Check BrainLink Client history for saved events!")


def ml_training_example():
    """Example: Collect training data for ML model"""
    print("=" * 60)
    print("🤖 ML Training Data Collection Example")
    print("=" * 60)
    print("\nThis example collects training data for ML model")
    print("Think different events - they will be added to ML training!")
    print()
    
    # Connect
    client = BrainLinkSharedMemoryClient()
    if not client.connect():
        return
    
    print("\n🎓 Training mode activated!")
    print("Press Ctrl+C when you have enough training samples")
    print("-" * 60)
    
    last_event = ""
    samples_collected = {}
    
    try:
        while True:
            event = client.get_event()
            
            if event and event != last_event:
                print(f"\n🧠 Event: {event}")
                
                # Send for ML training
                if client.send_event_for_ml_training(event):
                    samples_collected[event] = samples_collected.get(event, 0) + 1
                    print(f"   ✅ Added to ML training")
                    print(f"   📊 Samples: {samples_collected}")
                
                last_event = event
            
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\n\n🛑 Training collection stopped")
    
    finally:
        client.disconnect()
        print("\n📊 Training samples collected:")
        for event, count in samples_collected.items():
            print(f"   {event}: {count} samples")
        print("\n👋 Now you can train the model in BrainLink Client!")


def game_with_feedback_example():
    """Advanced: Game that provides feedback to player"""
    print("=" * 60)
    print("🎮 Interactive Game with Feedback")
    print("=" * 60)
    print("\nThis game:")
    print("  - Shows your attention/meditation levels")
    print("  - Responds to your thoughts")
    print("  - Saves successful moves to history")
    print("  - Only saves when attention is high!")
    print()
    
    client = BrainLinkSharedMemoryClient()
    if not client.connect():
        return
    
    print("\n🎮 Game started!")
    print("Move with high attention to save to history!")
    print("Press Ctrl+C to exit")
    print("-" * 60)
    
    player_x, player_y = 50, 50
    score = 0
    last_event = ""
    
    try:
        while True:
            # Read data
            attention = client.get_attention()
            meditation = client.get_meditation()
            event = client.get_event()
            
            # Display status every second
            if int(time.time()) % 5 == 0:
                print(f"\n📊 Status: Attention={attention}, Meditation={meditation}")
                print(f"   Position: ({player_x}, {player_y}), Score: {score}")
            
            # Process event
            if event and event != last_event:
                print(f"\n🎯 Event: {event}")
                
                # Move player
                moved = False
                if event == "ml":
                    player_x -= 10
                    moved = True
                    print("   ← Moved LEFT")
                elif event == "mr":
                    player_x += 10
                    moved = True
                    print("   → Moved RIGHT")
                elif event == "mu":
                    player_y -= 10
                    moved = True
                    print("   ↑ Moved UP")
                elif event == "md":
                    player_y += 10
                    moved = True
                    print("   ↓ Moved DOWN")
                
                # Save to history only if attention is high
                if moved:
                    if attention >= 60:
                        client.send_event_to_history(event)
                        score += 10
                        print(f"   ✅ GOOD MOVE! Saved to history (score +10)")
                    else:
                        print(f"   ⚠️ Low attention ({attention}), not saved")
                
                last_event = event
            
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\n\n🛑 Game stopped")
    
    finally:
        client.disconnect()
        print(f"\n📊 Final Stats:")
        print(f"   Position: ({player_x}, {player_y})")
        print(f"   Score: {score}")
        print("👋 Thanks for playing!")


def auto_labeling_example():
    """Advanced: Auto-label events based on game state"""
    print("=" * 60)
    print("🏷️ Auto-Labeling Example")
    print("=" * 60)
    print("\nThis example automatically labels events based on game state")
    print("Useful for collecting training data during gameplay!")
    print()
    
    client = BrainLinkSharedMemoryClient()
    if not client.connect():
        return
    
    print("\n🎮 Auto-labeling game started!")
    print("Game will detect when you're thinking and save events")
    print("Press Ctrl+C to exit")
    print("-" * 60)
    
    # Game state
    player_x = 50
    target_x = 80  # Player should move right
    
    print(f"\n🎯 Target: Move from X={player_x} to X={target_x}")
    print("Think 'Move Right' to reach the target!")
    
    last_event = ""
    saved_count = 0
    
    try:
        while player_x < target_x:
            event = client.get_event()
            attention = client.get_attention()
            
            if event and event != last_event:
                print(f"\n🎯 Event: {event}")
                
                # Move player
                if event == "mr":
                    player_x += 10
                    print(f"   → Moved to X={player_x}")
                    
                    # Save correct moves for ML training
                    if attention >= 50:
                        client.send_event_for_ml_training("mr")
                        saved_count += 1
                        print(f"   ✅ Saved as ML training sample (total: {saved_count})")
                    
                    if player_x >= target_x:
                        print(f"\n🎉 TARGET REACHED!")
                        break
                
                elif event in ["ml", "mu", "md"]:
                    print(f"   ⚠️ Wrong direction! (need 'mr')")
                
                last_event = event
            
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\n\n🛑 Stopped by user")
    
    finally:
        client.disconnect()
        print(f"\n📊 Collected {saved_count} ML training samples for 'mr' event")
        print("👋 This data will help train the ML model!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "simple":
            simple_example()
        elif mode == "ml":
            ml_training_example()
        elif mode == "game":
            game_with_feedback_example()
        elif mode == "auto":
            auto_labeling_example()
        else:
            print("Usage: python bidirectional_example.py [simple|ml|game|auto]")
    else:
        # Default: simple example
        simple_example()
