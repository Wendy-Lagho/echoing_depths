import pygame
import math
import random
import numpy as np
import pygame.sndarray

# Screen Dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRID_SIZE = 40

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
RED = (255, 0, 0)

# Game Parameters
INITIAL_LIGHT_RADIUS = 200
LIGHT_DECAY_RATE = 1
EXIT_PROXIMITY_THRESHOLD = 100

def generate_exit_hint_sound():
    """Generate a high-pitched beeping sound for exit proximity"""
    sample_rate = 44100
    duration = 0.3  # shorter duration
    frequency = 880.0  # High pitch (A5 note)
    
    # Generate a sine wave with periodic pulses
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = np.sin(2 * np.pi * frequency * t) * (np.sin(2 * np.pi * 5 * t) > 0) * 0.3
    
    # Create a stereo sound array (duplicate the mono channel)
    stereo_tone = np.column_stack((tone, tone))
    
    # Convert to 16-bit sound
    sound_array = (stereo_tone * 32767).astype(np.int16)
    sound = pygame.sndarray.make_sound(sound_array)
    return sound

def generate_wall_collision_sound():
    """Generate a low-pitched buzz for wall collisions"""
    sample_rate = 44100
    duration = 0.1  # Very short duration
    frequency = 220.0  # Lower pitch (A3 note)
    
    # Generate a harsh, short sound
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = np.sin(2 * np.pi * frequency * t) * np.sin(2 * np.pi * 10 * frequency * t) * 0.5
    
    # Create a stereo sound array (duplicate the mono channel)
    stereo_tone = np.column_stack((tone, tone))
    
    # Convert to 16-bit sound
    sound_array = (stereo_tone * 32767).astype(np.int16)
    sound = pygame.sndarray.make_sound(sound_array)
    return sound

class EchoingDepths:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        
        # Screen Setup
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Echoing Depths")
        
        # Game State
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Hardcoded Maze (1 = wall, 0 = path)
        self.maze = [
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 1, 1, 1, 1, 1, 1, 0, 1],
            [1, 0, 1, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 1, 0, 1, 1, 1, 1, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 1, 1, 1, 1, 1, 1, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        ]
        
        # Player & Exit Positions
        self.player_pos = [1 * GRID_SIZE, 1 * GRID_SIZE]
        self.exit_pos = [8 * GRID_SIZE, 7 * GRID_SIZE]
        
        # Light Mechanics
        self.light_radius = INITIAL_LIGHT_RADIUS
        
        # Sound Setup
        self.exit_sound = generate_exit_hint_sound()
        self.wall_sound = generate_wall_collision_sound()
        
        # Sound cooldown to prevent sound spam
        self.exit_sound_cooldown = 0
        self.wall_sound_cooldown = 0
        
    def draw_maze(self):
        for row in range(len(self.maze)):
            for col in range(len(self.maze[row])):
                if self.maze[row][col] == 1:
                    pygame.draw.rect(self.screen, GRAY, 
                        (col * GRID_SIZE, row * GRID_SIZE, GRID_SIZE, GRID_SIZE))
    
    def create_light_mask(self):
        # Create a circular light mask
        mask_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        mask_surface.fill((0, 0, 0, 255))
        
        pygame.draw.circle(mask_surface, (0, 0, 0, 0), 
                           (int(self.player_pos[0] + GRID_SIZE/2), 
                            int(self.player_pos[1] + GRID_SIZE/2)), 
                           int(self.light_radius))
        
        return mask_surface
    
    def play_proximity_sound(self):
        # Calculate distance to exit
        dx = abs(self.player_pos[0] - self.exit_pos[0])
        dy = abs(self.player_pos[1] - self.exit_pos[1])
        distance = math.sqrt(dx**2 + dy**2)
        
        # Manage sound cooldown
        if self.exit_sound_cooldown > 0:
            self.exit_sound_cooldown -= 1
        
        # Adjust sound based on proximity
        if distance <= EXIT_PROXIMITY_THRESHOLD and self.exit_sound_cooldown == 0:
            volume = 1 - (distance / EXIT_PROXIMITY_THRESHOLD)
            self.exit_sound.set_volume(volume)
            self.exit_sound.play()
            # Reset cooldown
            self.exit_sound_cooldown = 10
    
    def move_player(self, dx, dy):
        new_x = self.player_pos[0] + dx
        new_y = self.player_pos[1] + dy
        
        # Grid coordinates
        grid_x = new_x // GRID_SIZE
        grid_y = new_y // GRID_SIZE
        
        # Manage wall sound cooldown
        if self.wall_sound_cooldown > 0:
            self.wall_sound_cooldown -= 1
        
        # Collision detection
        if (0 <= grid_x < len(self.maze[0]) and 
            0 <= grid_y < len(self.maze) and 
            self.maze[grid_y][grid_x] == 0):
            self.player_pos[0] = new_x
            self.player_pos[1] = new_y
        else:
            # Play wall sound with cooldown
            if self.wall_sound_cooldown == 0:
                self.wall_sound.play()
                self.wall_sound_cooldown = 5
    
    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.move_player(-GRID_SIZE, 0)
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.move_player(GRID_SIZE, 0)
                    elif event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.move_player(0, -GRID_SIZE)
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.move_player(0, GRID_SIZE)
            
            # Reduce light radius
            self.light_radius = max(0, self.light_radius - LIGHT_DECAY_RATE)
            
            # Game over conditions
            if self.light_radius <= 0:
                print("Game Over - Light depleted!")
                self.running = False
            
            # Check exit condition
            if (abs(self.player_pos[0] - self.exit_pos[0]) < GRID_SIZE and 
                abs(self.player_pos[1] - self.exit_pos[1]) < GRID_SIZE):
                print("Congratulations! You reached the exit!")
                self.running = False
            
            # Play proximity sounds
            self.play_proximity_sound()
            
            # Clear screen
            self.screen.fill(BLACK)
            
            # Draw maze
            self.draw_maze()
            
            # Draw exit
            pygame.draw.rect(self.screen, RED, 
                             (self.exit_pos[0], self.exit_pos[1], GRID_SIZE, GRID_SIZE))
            
            # Draw player
            pygame.draw.rect(self.screen, WHITE, 
                             (self.player_pos[0], self.player_pos[1], GRID_SIZE, GRID_SIZE))
            
            # Apply light mask
            light_mask = self.create_light_mask()
            self.screen.blit(light_mask, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
            
            # Update display
            pygame.display.flip()
            self.clock.tick(10)  # Control game speed
        
        pygame.quit()

# Run the game
if __name__ == "__main__":
    game = EchoingDepths()
    game.run()