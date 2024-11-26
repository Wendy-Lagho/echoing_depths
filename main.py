import pygame
import math
import random
import numpy as np
import pygame.sndarray

# Import maze levels
from maze_level_1 import MAZE_1, PLAYER_START_1, EXIT_POS_1
from maze_level_2 import MAZE_2, PLAYER_START_2, EXIT_POS_2
from maze_level_3 import MAZE_3, PLAYER_START_3, EXIT_POS_3
from maze_level_4 import MAZE_4, PLAYER_START_4, EXIT_POS_4

# Screen Dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRID_SIZE = 40

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# Game Parameters
INITIAL_LIGHT_RADIUS = 200
LIGHT_DECAY_RATE = 5
EXIT_PROXIMITY_THRESHOLD = 100

class SoundManager:
    @staticmethod
    def generate_proximity_sound(min_freq=200, max_freq=800):
        """Generate a sound based on proximity to exit"""
        sample_rate = 44100
        duration = 0.2  # Short beep
        
        # Create a varying frequency tone
        t = np.linspace(0, duration, int(sample_rate * duration), False)

        # Generate stereo sound (2 channels)
        freq = np.random.uniform(min_freq, max_freq)
        tone_left = np.sin(2 * np.pi * freq * t) * 0.25
        tone_right = np.sin(2 * np.pi * freq * t) * 0.25
    
        # Combine into a 2D array (stereo) and ensure C-contiguous
        stereo_tone = np.ascontiguousarray(np.vstack((tone_left, tone_right)).T)
        
        # Convert to 16-bit sound
        sound_array = np.ascontiguousarray((stereo_tone * 32767).astype(np.int16))
        return pygame.sndarray.make_sound(sound_array)
    
    @staticmethod
    def generate_wall_collision_sound():
        """Generate a stereo wall collision sound"""
        sample_rate = 44100
        duration = 0.1  # Very short buzz
        frequency = 100.0  # Low pitch
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # Generate stereo sound
        tone_left = np.sin(2 * np.pi * frequency * t) * 0.3
        tone_right = np.sin(2 * np.pi * frequency * t) * 0.3

        
        # Combine into a 2D array (stereo) and ensure C-contiguous
        stereo_tone = np.ascontiguousarray(np.vstack((tone_left, tone_right)).T)
    
        # Convert to 16-bit sound
        sound_array = np.ascontiguousarray((stereo_tone * 32767).astype(np.int16))
        return pygame.sndarray.make_sound(sound_array)

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
        self.current_level = 1
        
        # Level Setup
        self.setup_level()
        
        # Light Mechanics
        self.light_radius = INITIAL_LIGHT_RADIUS
        
        # Sound Setup
        self.proximity_sound = SoundManager.generate_proximity_sound()
        self.wall_sound = SoundManager.generate_wall_collision_sound()
        self.exit_sound = pygame.mixer.Sound(
            pygame.sndarray.make_sound(
                np.ascontiguousarray(
                    np.vstack((
                        np.sin(2 * np.pi * np.arange(44100) * 880.0 / 44100.0) * 127 + 128,
                        np.sin(2 * np.pi * np.arange(44100) * 880.0 / 44100.0) * 127 + 128
                    )).T.astype(np.uint8)
                )
            )
        )
        
    def setup_level(self):
        """Setup the current level's maze and positions"""
        if self.current_level == 1:
            self.maze = MAZE_1
            self.player_pos = PLAYER_START_1.copy()
            self.exit_pos = EXIT_POS_1
        elif self.current_level == 2:
            self.maze = MAZE_2
            self.player_pos = PLAYER_START_2.copy()
            self.exit_pos = EXIT_POS_2
        elif self.current_level == 3:
            self.maze = MAZE_3
            self.player_pos = PLAYER_START_3.copy()
            self.exit_pos = EXIT_POS_3
        elif self.current_level == 4:
            self.maze = MAZE_4
            self.player_pos = PLAYER_START_4.copy()
            self.exit_pos = EXIT_POS_4
        else:
            print("Congratulations! You completed all levels!")
            self.running = False
        
        # Reset light for new level
        self.light_radius = INITIAL_LIGHT_RADIUS
    
    def play_proximity_sound(self):
        """Play sound hints based on proximity to exit"""
        dx = abs(self.player_pos[0] - self.exit_pos[0])
        dy = abs(self.player_pos[1] - self.exit_pos[1])
        distance = math.sqrt(dx**2 + dy**2)
        
        # Play sound if within proximity threshold
        if distance <= EXIT_PROXIMITY_THRESHOLD:
            # Adjust volume based on distance
            volume = 1 - (distance / EXIT_PROXIMITY_THRESHOLD)
            self.proximity_sound.set_volume(volume)
            self.proximity_sound.play()
    
    def move_player(self, dx, dy):
        new_x = self.player_pos[0] + dx
        new_y = self.player_pos[1] + dy
        
        # Grid coordinates
        grid_x = new_x // GRID_SIZE
        grid_y = new_y // GRID_SIZE
        
        # Collision detection
        if (0 <= grid_x < len(self.maze[0]) and 
            0 <= grid_y < len(self.maze) and 
            self.maze[grid_y][grid_x] == 0):
            self.player_pos[0] = new_x
            self.player_pos[1] = new_y
            
            # Reduce light with each move
            self.light_radius = max(0, self.light_radius - LIGHT_DECAY_RATE)
        else:
            self.wall_sound.play()
    
    def draw_maze(self):
        for row in range(len(self.maze)):
            for col in range(len(self.maze[row])):
                if self.maze[row][col] == 1:
                    pygame.draw.rect(self.screen, GRAY, 
                        (col * GRID_SIZE, row * GRID_SIZE, GRID_SIZE, GRID_SIZE))
    
    def create_light_mask(self):
        # Create a circular light mask with dynamic pulsing
        mask_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        mask_surface.fill((0, 0, 0, 255))
        
        # Add a pulsing effect similar to the Phaser implementation
        current_time = pygame.time.get_ticks()
        pulse_factor = math.cos(current_time * 0.005)  # Slower, smoother oscillation
        
        # Dynamic radius: base radius + pulsing component
        dynamic_radius = int(self.light_radius + 20 * pulse_factor)
        
        # Create a radial gradient for more natural light falloff
        for r in range(dynamic_radius, 0, -10):
            alpha = int(255 * (1 - r / dynamic_radius))
            gradient_surface = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            
            # Radial gradient
            for x in range(r*2):
                for y in range(r*2):
                    distance = math.sqrt((x-r)**2 + (y-r)**2)
                    if distance <= r:
                        gradient_alpha = max(0, 255 * (1 - distance/r))
                        gradient_surface.set_at((x, y), (255, 255, 255, int(gradient_alpha)))
            
            pygame.draw.circle(mask_surface, (0, 0, 0, alpha), 
                               (int(self.player_pos[0] + GRID_SIZE/2), 
                                int(self.player_pos[1] + GRID_SIZE/2)), 
                               r)
        
        return mask_surface
    
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
            
            # Game over conditions
            if self.light_radius <= 0:
                print(f"Game Over - Light depleted in Level {self.current_level}!")
                self.running = False
            
            # Check exit condition
            if (abs(self.player_pos[0] - self.exit_pos[0]) < GRID_SIZE and 
                abs(self.player_pos[1] - self.exit_pos[1]) < GRID_SIZE):
                print(f"Level {self.current_level} Completed!")
                self.exit_sound.play()
                
                # Progress to next level
                self.current_level += 1
                self.setup_level()
                
                # If no more levels, game ends
                if not self.running:
                    break
            
            # Play proximity sounds
            self.play_proximity_sound()
            
            # Clear screen
            self.screen.fill(BLACK)
            
            # Draw maze
            self.draw_maze()
            
            # Draw exit
            pygame.draw.rect(self.screen, GREEN, 
                             (self.exit_pos[0], self.exit_pos[1], GRID_SIZE, GRID_SIZE))
            # Draw player
            pygame.draw.rect(self.screen, WHITE, 
                             (self.player_pos[0], self.player_pos[1], GRID_SIZE, GRID_SIZE))
            
            # Apply light mask
            light_mask = self.create_light_mask()
            self.screen.blit(light_mask, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
            
            # Display current level and light radius
            font = pygame.font.Font(None, 36)
            level_text = font.render(f"Level: {self.current_level}", True, WHITE)
            light_text = font.render(f"Light: {int(self.light_radius)}", True, WHITE)
            self.screen.blit(level_text, (10, 10))
            self.screen.blit(light_text, (10, 50))
            
            # Update display
            pygame.display.flip()
            self.clock.tick(10)  # Control game speed
        
        pygame.quit()

# Run the game
if __name__ == "__main__":
    game = EchoingDepths()
    game.run()