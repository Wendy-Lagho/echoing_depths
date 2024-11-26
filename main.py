import pygame
import numpy as np
import math
import random
import pygame.mixer

# Screen and Game Constants
SCREEN_WIDTH = 800  # Reduced screen width
SCREEN_HEIGHT = 600  # Reduced screen height
SCREEN_TITLE = "Echoing Depths: Sound-Navigated Maze Survival"
GRID_SIZE = 40  # Slightly smaller grid size
MOVEMENT_SPEED = 3
FPS = 60

# Color Constants
WALL_COLOR = (50, 50, 50)
PLAYER_COLOR = (255, 255, 255)
EXIT_COLOR = (0, 255, 0)
BACKGROUND_COLOR = (0, 0, 0)
DARK_OVERLAY_COLOR = (0, 0, 0, 220)  # Darker, more opaque overlay

class MazeGenerator:
    @staticmethod
    def generate_maze(width, height):
        """Generate a simplified maze with guaranteed paths"""
        maze = [['#' for _ in range(width)] for _ in range(height)]
        
        def in_bounds(x, y):
            return 0 <= x < width and 0 <= y < height
        
        def carve_passages(x, y):
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            random.shuffle(directions)
            
            for dx, dy in directions:
                nx, ny = x + dx*2, y + dy*2
                if in_bounds(nx, ny) and maze[ny][nx] == '#':
                    maze[y+dy][x+dx] = ' '
                    maze[ny][nx] = ' '
                    carve_passages(nx, ny)
        
        maze[1][1] = 'P'  # Player start
        carve_passages(1, 1)
        
        maze[height-2][width-2] = 'E'
        
        return [''.join(row) for row in maze]

class LightEngine:
    def __init__(self, screen_width, screen_height):
        """Initialize light engine with dynamic light parameters"""
        self.light_radius = 200  # Base light radius
        self.light_color = (255, 255, 200)  # Warm, slightly yellow light
        self.flicker_intensity = 10  # Light radius variation
        self.noise_time = 0

        # Initialize sound
        pygame.mixer.init()
        self.buzz_sound = pygame.mixer.Sound('buzz.wav')  # Load your sound file
        self.buzz_sound.set_volume(0)  # Start with volume at 0
        self.light_timer = 0  # Timer for light duration
        self.light_duration = 10  # Duration in seconds before darkness
        
    def create_light_surface(self, player_pos):
        """Create a dynamic light surface with radial gradient"""
        # Create a surface for the light effect
        light_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        
        # Add slight noise-based flickering
        self.noise_time += 0.1
        flicker = math.sin(self.noise_time) * self.flicker_intensity
        current_radius = self.light_radius + flicker
        
        # Create radial gradient
        for alpha in range(int(current_radius), 0, -5):
            # Calculate alpha value for gradient (fade out)
            gradient_alpha = int(255 * (1 - alpha / current_radius))
            
            # Create color with decreasing alpha
            light_color = self.light_color + (gradient_alpha,)
            
            # Draw concentric circles with decreasing alpha
            pygame.draw.circle(light_surface, light_color, 
                               player_pos, 
                               alpha)
        
        return light_surface

class EchoingDepthsGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(SCREEN_TITLE)
        self.clock = pygame.time.Clock()
        
        # Game state
        self.wall_list = []
        self.player_pos = None
        self.exit_pos = None
        
        # Light engine
        self.light_engine = LightEngine(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # Initialize level
        self.setup_level()

        self.light_timer = 0  # Initialize light_timer
        self.light_duration = 100
    
    def setup_level(self):
        """Initialize a new game level"""
        # Generate maze with more open spaces
        maze = MazeGenerator.generate_maze(width=20, height=15)
        self.wall_list = []
        
        for row_index, row in enumerate(maze):
            for col_index, cell in enumerate(row):
                # Calculate precise grid positions
                x = col_index * GRID_SIZE
                y = row_index * GRID_SIZE
                
                if cell == '#':
                    # Create wall with full grid size
                    self.wall_list.append(pygame.Rect(x, y, GRID_SIZE, GRID_SIZE))
                
                elif cell == 'P':
                    # Player start position (center of grid cell)
                    self.player_pos = pygame.Vector2(
                        x + GRID_SIZE // 2, 
                        y + GRID_SIZE // 2
                    )
                
                elif cell == 'E':
                    # Exit position
                    self.exit_pos = pygame.Vector2(
                        x + GRID_SIZE // 2, 
                        y + GRID_SIZE // 2
                    )
    
    def handle_movement(self):
        """Handle player movement with collision detection"""
        keys = pygame.key.get_pressed()
        move_vector = pygame.Vector2(0, 0)
        
        # Movement input
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            move_vector.y -= MOVEMENT_SPEED
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            move_vector.y += MOVEMENT_SPEED
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move_vector.x -= MOVEMENT_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_vector.x += MOVEMENT_SPEED
        
        # No movement if no keys pressed
        if move_vector.length() == 0:
            return
        
        # Normalize movement
        if move_vector.length() > 0:
            move_vector = move_vector.normalize() * MOVEMENT_SPEED
        
        # Propose new position
        new_pos = self.player_pos + move_vector
        
        # Create collision rect
        player_rect = pygame.Rect(
            new_pos.x - GRID_SIZE//4, 
            new_pos.y - GRID_SIZE//4, 
            GRID_SIZE//2, 
            GRID_SIZE//2
        )
        
        # Check for wall collisions
        if not any(player_rect.colliderect(wall) for wall in self.wall_list):
            self.player_pos = new_pos
    
    def play(self):
        """Main game loop"""
        running = True
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Update light timer
            if self.light_timer < self.light_duration:
                self.light_timer += 1 / FPS  # Increment timer based on frame rate

            # Clear screen with dark background
            self.screen.fill(BACKGROUND_COLOR)

            # Handle player movement
            self.handle_movement()

            # Draw walls
            for wall in self.wall_list:
                pygame.draw.rect(self.screen, WALL_COLOR, wall)

            # Draw exit
            exit_rect = pygame.Rect(self.exit_pos.x - GRID_SIZE//4, 
                                    self.exit_pos.y - GRID_SIZE//4, 
                                    GRID_SIZE//2, 
                                    GRID_SIZE//2)
            pygame.draw.rect(self.screen, EXIT_COLOR, exit_rect)

            # Create dark overlay
            dark_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            dark_overlay.fill(DARK_OVERLAY_COLOR)

            # Create and apply light effect if within duration
            if self.light_timer < self.light_duration:
                light_surface = self.light_engine.create_light_surface(
                    (int(self.player_pos.x), int(self.player_pos.y))
                )
                dark_overlay.blit(light_surface, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

                # Calculate distance to exit for sound
                distance_to_exit = self.player_pos.distance_to(self.exit_pos)
                max_distance = SCREEN_WIDTH  # Maximum distance for sound volume calculation
                volume = max(0, min(1, 1 - (distance_to_exit / max_distance)) )  # Normalize volume
                self.light_engine.buzz_sound.set_volume(volume)
                self.light_engine.buzz_sound.play(-1)  # Loop the sound
            else:
                # If light duration has passed, stop the sound and set volume to 0
                self.light_engine.buzz_sound.stop()
                self.light_engine.buzz_sound.set_volume(0)

            # Draw player
            pygame.draw.rect(self.screen, PLAYER_COLOR, 
                             pygame.Rect(self.player_pos.x - GRID_SIZE//4, 
                                         self.player_pos.y - GRID_SIZE//4, 
                                         GRID_SIZE//2, 
                                         GRID_SIZE//2))

            # Apply dark overlay
            self.screen.blit(dark_overlay, (0, 0))

            # Update display
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()

def main():
    """Main game initialization"""
    game = EchoingDepthsGame()
    game.play()

if __name__ == "__main__":
    main()