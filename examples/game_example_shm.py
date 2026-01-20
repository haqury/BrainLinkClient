"""
Game Integration Example using Shared Memory

This example shows how to integrate BrainLink into a game using Shared Memory
for ultra-fast performance (~0.01ms latency).

Perfect for Python games like pygame, arcade, panda3d, etc.
"""

from multiprocessing import shared_memory
import struct
import time


# Event codes (must match services/shared_memory_service.py)
EVENT_CODES = {
    0: "",
    1: "ml",    # Move Left
    2: "mr",    # Move Right
    3: "mu",    # Move Up
    4: "md",    # Move Down
    5: "stop",  # Stop
}


class BrainLinkGameClient:
    """Ultra-fast BrainLink client for games using Shared Memory"""
    
    # Memory offsets (int32)
    ATTENTION = 2
    MEDITATION = 3
    EVENT_CODE = 13
    GYRO_X = 14
    GYRO_Y = 15
    GYRO_Z = 16
    
    def __init__(self, memory_name="brainlink_data"):
        self.memory_name = memory_name
        self.shm = None
        self.connected = False
    
    def connect(self):
        """Connect to BrainLink shared memory"""
        try:
            self.shm = shared_memory.SharedMemory(name=self.memory_name)
            self.connected = True
            print("✅ Connected to BrainLink!")
            return True
        except FileNotFoundError:
            print("❌ BrainLink not found! Make sure it's running with Shared Memory enabled.")
            return False
    
    def disconnect(self):
        """Disconnect from shared memory"""
        if self.shm:
            self.shm.close()
        self.connected = False
    
    def _read_int(self, offset: int) -> int:
        """Read int32 from memory"""
        if not self.shm:
            return 0
        byte_offset = offset * 4
        return struct.unpack('i', self.shm.buf[byte_offset:byte_offset + 4])[0]
    
    def get_event(self) -> str:
        """Get current event (ultra-fast!)"""
        code = self._read_int(self.EVENT_CODE)
        return EVENT_CODES.get(code, "")
    
    def get_attention(self) -> int:
        """Get attention level (0-100)"""
        return self._read_int(self.ATTENTION)
    
    def get_meditation(self) -> int:
        """Get meditation level (0-100)"""
        return self._read_int(self.MEDITATION)
    
    def get_gyro(self) -> tuple:
        """Get gyro data (x, y, z)"""
        return (
            self._read_int(self.GYRO_X),
            self._read_int(self.GYRO_Y),
            self._read_int(self.GYRO_Z)
        )


# ==================== SIMPLE GAME EXAMPLE ====================

class SimpleGame:
    """Simple game controlled by BrainLink via Shared Memory"""
    
    def __init__(self):
        self.client = BrainLinkGameClient()
        
        # Game state
        self.player_x = 50
        self.player_y = 50
        self.score = 0
        self.running = False
    
    def run(self):
        """Run the game"""
        print("=" * 60)
        print("🎮 BrainLink Game - Shared Memory Edition")
        print("=" * 60)
        print("\n⚡ Ultra-fast mode: ~0.01ms latency!")
        print("\nControls:")
        print("  Think 'Move Left' → Player moves LEFT")
        print("  Think 'Move Right' → Player moves RIGHT")
        print("  Think 'Move Up' → Player moves UP")
        print("  Think 'Move Down' → Player moves DOWN")
        print("  Think 'Stop' → Player STOPS")
        print("\nPress Ctrl+C to exit")
        print("=" * 60)
        
        # Connect to BrainLink
        if not self.client.connect():
            print("\nMake sure BrainLink Client is running!")
            return
        
        self.running = True
        last_event = ""
        
        try:
            # Main game loop
            while self.running:
                # Read event (ultra-fast - only 1 field read!)
                event = self.client.get_event()
                
                # Process event if changed
                if event and event != last_event:
                    self.handle_event(event)
                    last_event = event
                
                # Sleep to avoid 100% CPU
                time.sleep(0.01)  # 100 FPS polling
        
        except KeyboardInterrupt:
            print("\n\n🛑 Game stopped by user")
        
        finally:
            self.client.disconnect()
            print(f"\n📊 Final Score: {self.score}")
            print(f"📍 Final Position: ({self.player_x}, {self.player_y})")
            print("👋 Thanks for playing!")
    
    def handle_event(self, event: str):
        """Handle BrainLink event"""
        print(f"\n🎯 Event: {event}")
        
        # Move player
        if event == "ml":  # Move Left
            self.player_x -= 10
            print("   ← Player moved LEFT")
        
        elif event == "mr":  # Move Right
            self.player_x += 10
            print("   → Player moved RIGHT")
        
        elif event == "mu":  # Move Up
            self.player_y -= 10
            print("   ↑ Player moved UP")
        
        elif event == "md":  # Move Down
            self.player_y += 10
            print("   ↓ Player moved DOWN")
        
        elif event == "stop":  # Stop
            print("   ⏸ Player STOPPED")
        
        # Keep in bounds
        self.player_x = max(0, min(100, self.player_x))
        self.player_y = max(0, min(100, self.player_y))
        
        # Update score
        self.score += 10
        
        # Display status
        attention = self.client.get_attention()
        meditation = self.client.get_meditation()
        print(f"   Position: ({self.player_x}, {self.player_y})")
        print(f"   Score: {self.score}")
        print(f"   Attention: {attention}, Meditation: {meditation}")


# ==================== ADVANCED EXAMPLE ====================

class AdvancedGame:
    """Advanced game using attention/meditation for game mechanics"""
    
    def __init__(self):
        self.client = BrainLinkGameClient()
        self.player_x = 50
        self.player_y = 50
        self.speed = 5
        self.shield_active = False
    
    def run(self):
        if not self.client.connect():
            return
        
        print("\n🎮 Advanced Game Mode:")
        print("   - Attention affects speed")
        print("   - Meditation activates shield")
        print()
        
        try:
            while True:
                # Read data
                event = self.client.get_event()
                attention = self.client.get_attention()
                meditation = self.client.get_meditation()
                
                # Speed based on attention (25-100% speed)
                self.speed = 5 + (attention / 100 * 10)
                
                # Shield based on meditation
                self.shield_active = (meditation > 70)
                
                # Move based on event
                if event:
                    self.move(event, self.speed)
                
                time.sleep(0.01)
        
        except KeyboardInterrupt:
            pass
        finally:
            self.client.disconnect()
    
    def move(self, event: str, speed: float):
        """Move player with variable speed"""
        if event == "ml":
            self.player_x -= speed
        elif event == "mr":
            self.player_x += speed
        elif event == "mu":
            self.player_y -= speed
        elif event == "md":
            self.player_y += speed
        
        shield_status = "🛡️ ON" if self.shield_active else "⚫ OFF"
        print(f"{event}: Position ({self.player_x:.1f}, {self.player_y:.1f}), "
              f"Speed: {speed:.1f}, Shield: {shield_status}")


# ==================== PYGAME EXAMPLE ====================

def pygame_example():
    """
    Example integration with pygame
    
    Note: This is a template. Install pygame first:
    pip install pygame
    """
    print("\n📝 Pygame integration example:\n")
    
    example_code = '''
import pygame
from shared_memory_client import BrainLinkGameClient

# Initialize
pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

# BrainLink client
brainlink = BrainLinkGameClient()
brainlink.connect()

# Game state
player_x, player_y = 400, 300
running = True

# Game loop
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # Get BrainLink event (ultra-fast!)
    bl_event = brainlink.get_event()
    
    # Move player based on event
    if bl_event == "ml":
        player_x -= 5
    elif bl_event == "mr":
        player_x += 5
    elif bl_event == "mu":
        player_y -= 5
    elif bl_event == "md":
        player_y += 5
    
    # Draw
    screen.fill((0, 0, 0))
    pygame.draw.circle(screen, (0, 255, 0), (player_x, player_y), 20)
    pygame.display.flip()
    clock.tick(60)  # 60 FPS

brainlink.disconnect()
pygame.quit()
'''
    
    print(example_code)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "pygame":
        pygame_example()
    else:
        # Run simple game
        game = SimpleGame()
        game.run()
