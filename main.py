import pygame
import numpy as np
import math
import random
import pygame.mixer
import os
import time

# Screen and Game Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Echoing Depths: Sound-Navigated Maze Survival"
GRID_SIZE = 40
MOVEMENT_SPEED = 3
FPS = 60

# Color Constants
WALL_COLOR = (50, 50, 50)
PLAYER_COLOR = (200, 200, 255)  # Soft bluish white
EXIT_COLOR = (50, 255, 50)  # Vibrant green
BACKGROUND_COLOR = (10, 10, 20)  # Deep dark blue-black
DARK_OVERLAY_COLOR = (0, 0, 0, 220)

class MazeGenerator:
    @staticmethod
    def generate_maze(width, height, complexity=0):
        """Generate a maze with optional complexity parameter and more organic feel"""
        maze = [['#' for _ in range(width)] for _ in range(height)]
        
        def in_bounds(x, y):
            return 0 <= x < width and 0 <= y < height
        
        def carve_passages(x, y):
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            random.shuffle(directions)
            
            for dx, dy in directions:
                nx, ny = x + dx*2, y + dy*2
                if in_bounds(nx, ny) and maze[ny][nx] == '#':
                    # Add some randomness to path creation
                    if random.random() > 0.1:  # 90% chance of carving
                        maze[y+dy][x+dx] = ' '
                        maze[ny][nx] = ' '
                        carve_passages(nx, ny)
        
        maze[1][1] = 'P'  # Player start
        carve_passages(1, 1)
        
        maze[height-2][width-2] = 'E'
        
        return [''.join(row) for row in maze]

class LightEngine:
    def __init__(self, screen_width, screen_height, darkness_level=1):
        """Initialize light engine with more dynamic light parameters"""
        self.light_radius = max(50, 200 - (darkness_level * 50))
        self.light_color = (255, 240, 200)  # Warm, slightly yellow light
        self.flicker_intensity = 15
        self.noise_time = 0

        pygame.mixer.init()
        
        try:
            self.buzz_sound = pygame.mixer.Sound('buzz.wav')
        except pygame.error:
            print("Warning: Could not load 'buzz.wav'. Using a silent sound.")
            self.buzz_sound = pygame.mixer.Sound(buffer=bytes(1000))
        
        self.buzz_sound.set_volume(0)
        self.light_timer = 0
        self.light_duration = 20  # Initial light duration set to 20 seconds
        
    def create_light_surface(self, player_pos):
        """Create a more organic light surface with soft edges and glow"""
        light_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        
        self.noise_time += 0.1
        # More pronounced flicker with sine and cosine for organic movement
        flicker_x = math.sin(self.noise_time) * self.flicker_intensity
        flicker_y = math.cos(self.noise_time) * self.flicker_intensity
        current_radius = self.light_radius + abs(flicker_x)
        
        # Create multiple layers of gradually transparent circles
        for alpha in range(int(current_radius), 0, -10):
            gradient_alpha = int(255 * (1 - alpha / current_radius))
            light_color = self.light_color + (gradient_alpha,)
            
            # Slightly offset the center for more organic feel
            offset_pos = (
                player_pos[0] + flicker_x * 0.1, 
                player_pos[1] + flicker_y * 0.1
            )
            
            pygame.draw.circle(light_surface, light_color, 
                               offset_pos, 
                               alpha)
        
        return light_surface

class EchoingDepthsGame:
    def __init__(self, starting_level=1):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(SCREEN_TITLE)
        self.clock = pygame.time.Clock()
        
        # Game progression
        self.current_level = starting_level
        self.max_levels = 5  # Increased number of levels
        
        # Game state
        self.wall_list = []
        self.player_pos = None
        self.exit_pos = None
        
        # Font for level display
        self.font = pygame.font.Font(None, 36)
        
        # Light engine with increasing darkness
        self.light_engine = LightEngine(SCREEN_WIDTH, SCREEN_HEIGHT, 
                                        darkness_level=self.current_level)
        
        # Initialize level
        self.setup_level()

        self.light_timer = 0
        self.light_duration = max(10, 20 - (self.current_level * 2))  # Decrease light duration with each level
        
        # Game result tracking
        self.game_over = False
        self.game_won = False

        # Particle system for visual effects
        self.particles = []

        # Track start time
        self.start_time = time.time()
        
        # Score tracking
        self.total_score = 0
    
    def create_wall_texture(self, wall_rect):
        """Create a textured surface for walls"""
        texture = pygame.Surface((GRID_SIZE, GRID_SIZE))
        
        # Base wall color with variation
        base_color = (random.randint(40, 60), random.randint(40, 60), random.randint(40, 60))
        texture.fill(base_color)
        
        # Add some noise/texture
        for _ in range(50):
            x = random.randint(0, GRID_SIZE-1)
            y = random.randint(0, GRID_SIZE-1)
            shade = random.randint(-20, 20)
            noise_color = tuple(max(0, min(255, base_color[i] + shade)) for i in range(3))
            texture.set_at((x, y), noise_color)
        
        return texture

    def setup_level(self):
        """Initialize a new game level with more complex generation"""
        max_maze_width = SCREEN_WIDTH // GRID_SIZE
        max_maze_height = SCREEN_HEIGHT // GRID_SIZE
        
        maze_width = min(20 + (self.current_level * 2), max_maze_width)
        maze_height = min(15 + self.current_level, max_maze_height)
        
        maze = MazeGenerator.generate_maze(
            width=maze_width, 
            height=maze_height, 
            complexity=self.current_level - 1
        )
        
        self.wall_list = []
        self.wall_textures = []  # Store wall textures
        
        for row_index, row in enumerate(maze):
            for col_index, cell in enumerate(row):
                x = col_index * GRID_SIZE
                y = row_index * GRID_SIZE
                
                if cell == '#':
                    wall_rect = pygame.Rect(x, y, GRID_SIZE, GRID_SIZE)
                    self.wall_list.append(wall_rect)
                    # Create and store a unique texture for each wall
                    self.wall_textures.append(self.create_wall_texture(wall_rect))
                
                elif cell == 'P':
                    self.player_pos = pygame.Vector2(
                        x + GRID_SIZE // 2, 
                        y + GRID_SIZE // 2
                    )
                
                elif cell == 'E':
                    self.exit_pos = pygame.Vector2(
                        x + GRID_SIZE // 2, 
                        y + GRID_SIZE // 2
                    )
        
        # Reset start time for the new level
        self.start_time = time.time()
    
    def create_player_particle(self):
        """Create particles around the player for a glowing effect"""
        for _ in range(2):
            particle = {
                'pos': pygame.Vector2(
                    self.player_pos.x + random.uniform(-10, 10),
                    self.player_pos.y + random.uniform(-10, 10)
                ),
                'velocity': pygame.Vector2(
                    random.uniform(-1, 1),
                    random.uniform(-1, 1)
                ),
                'color': (200, 200, 255, 100),
                'size': random.uniform(2, 5),
                'lifetime': random.uniform(0.5, 1.5)
            }
            self.particles.append(particle)
    
    def update_particles(self):
        """Update and render particles"""
        for particle in self.particles[:]:
            particle['pos'] += particle['velocity']
            particle['lifetime'] -= 1 / FPS
            
            if particle['lifetime'] <= 0:
                self.particles.remove(particle)
    
    def draw_particles(self):
        """Draw particles on screen"""
        for particle in self.particles:
            pygame.draw.circle(
                self.screen, 
                particle['color'], 
                (int(particle['pos'].x), int(particle['pos'].y)), 
                int(particle['size'])
            )

    def handle_movement(self):
        """Handle player movement with collision detection"""
        keys = pygame.key.get_pressed()
        move_vector = pygame.Vector2(0, 0)
        
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            move_vector.y -= MOVEMENT_SPEED
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            move_vector.y += MOVEMENT_SPEED
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move_vector.x -= MOVEMENT_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_vector.x += MOVEMENT_SPEED
        
        if move_vector.length() == 0:
            return
        
        if move_vector.length() > 0:
            move_vector = move_vector.normalize() * MOVEMENT_SPEED
        
        new_pos = self.player_pos + move_vector
        
        player_rect = pygame.Rect(
            new_pos.x - GRID_SIZE//4, 
            new_pos.y - GRID_SIZE//4, 
            GRID_SIZE//2, 
            GRID_SIZE//2
        )
        
        if not any(player_rect.colliderect(wall) for wall in self.wall_list):
            self.player_pos = new_pos
            # Create player movement particles
            self.create_player_particle()
    
    def check_level_completion(self):
        """Check if the player has reached the exit"""
        if self.player_pos.distance_to(self.exit_pos) < GRID_SIZE // 2:
            self.game_won = True
            self.game_over = True
            print(f"Level {self.current_level} completed!")

    def display_level_completion(self):
        """Display level completion message with time taken and score"""
        time_taken = time.time() - self.start_time
        score = self.calculate_score(time_taken)
        self.total_score += score
        message = self.font.render(f"Level {self.current_level} Completed!", True, (255, 255, 255))
        time_message = self.font.render(f"Time: {time_taken:.2f} seconds", True, (255, 255, 255))
        score_message = self.font.render(f"Score: {score}", True, (255, 255, 255))
        total_score_message = self.font.render(f"Total Score: {self.total_score}", True, (255, 255, 255))
        
        self.screen.blit(message, (SCREEN_WIDTH // 2 - message.get_width() // 2, SCREEN_HEIGHT // 2 - message.get_height() // 2 - 60))
        self.screen.blit(time_message, (SCREEN_WIDTH // 2 - time_message.get_width() // 2, SCREEN_HEIGHT // 2 - time_message.get_height() // 2 - 20))
        self.screen.blit(score_message, (SCREEN_WIDTH // 2 - score_message.get_width() // 2, SCREEN_HEIGHT // 2 - score_message.get_height() // 2 + 20))
        self.screen.blit(total_score_message, (SCREEN_WIDTH // 2 - total_score_message.get_width() // 2, SCREEN_HEIGHT // 2 - total_score_message.get_height() // 2 + 60))
        
        pygame.display.flip()
        pygame.time.wait(2000)  # Wait for 2 seconds

    def display_game_over(self):
        """Display game over message"""
        message = self.font.render("Game Over! Time's up!", True, (255, 0, 0))
        self.screen.blit(message, (SCREEN_WIDTH // 2 - message.get_width() // 2, SCREEN_HEIGHT // 2 - message.get_height() // 2))
        pygame.display.flip()
        pygame.time.wait(2000)  # Wait for 2 seconds

    def calculate_score(self, time_taken):
        """Calculate score based on time taken"""
        if time_taken < 5:
            return 100
        elif time_taken < 10:
            return 80
        elif time_taken < 15:
            return 60
        elif time_taken < 20:
            return 40
        else:
            return 20

    def draw_hud(self):
        """Draw the HUD with current level, score, and time"""
        time_taken = time.time() - self.start_time
        level_message = self.font.render(f"Level: {self.current_level}", True, (255, 255, 255))
        score_message = self.font.render(f"Score: {self.total_score}", True, (255, 255, 255))
        time_message = self.font.render(f"Time: {time_taken:.2f}", True, (255, 255, 255))
        
        self.screen.blit(level_message, (10, 10))
        self.screen.blit(score_message, (10, 40))
        self.screen.blit(time_message, (10, 70))

    def play(self):
        """Main game loop"""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            if not self.game_over:
                # Update light timer
                if self.light_timer < self.light_duration:
                    self.light_timer += 1 / FPS

                    # Sound guidance mechanics
                    distance_to_exit = self.player_pos.distance_to(self.exit_pos)
                    max_distance = SCREEN_WIDTH
                    volume = max(0, min(1, 1 - (distance_to_exit / max_distance)))
                    
                    self.light_engine.buzz_sound.set_volume(volume)
                    self.light_engine.buzz_sound.play(-1)
                else:
                    self.light_engine.buzz_sound.stop()
                    self.game_over = True
                    self.display_game_over()
                    running = False

                # Check for level completion
                self.check_level_completion()

                # Handle player movement
                self.handle_movement()

                # Update particles
                self.update_particles()

            # Clear screen with gradient background
            for y in range(SCREEN_HEIGHT):
                color = (10, 10, 20 + y // 3)
                pygame.draw.line(self.screen, color, (0, y), (SCREEN_WIDTH, y))

            # Draw walls with unique textures
            for wall, texture in zip(self.wall_list, self.wall_textures):
                # Blit the textured surface onto the screen
                self.screen.blit(texture, wall)

            # Draw exit with pulsing effect
            pulse = math.sin(pygame.time.get_ticks() * 0.01) * 20
            exit_rect = pygame.Rect(
                self.exit_pos.x - GRID_SIZE//4 + pulse, 
                self.exit_pos.y - GRID_SIZE//4 + pulse, 
                GRID_SIZE//2 - pulse*2, 
                GRID_SIZE//2 - pulse*2
            )
            pygame.draw.rect(self.screen, EXIT_COLOR, exit_rect)

            # Create dark overlay
            dark_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            dark_overlay.fill(DARK_OVERLAY_COLOR)

            # Create and apply light effect
            if not self.game_over and self.light_timer < self.light_duration:
                light_surface = self.light_engine.create_light_surface(
                    (int(self.player_pos.x), int(self.player_pos.y))
                )
                dark_overlay.blit(light_surface, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

            # Draw player with glow
            pygame.draw.circle(
                self.screen, 
                PLAYER_COLOR, 
                (int(self.player_pos.x), int(self.player_pos.y)), 
                GRID_SIZE//3
            )

            # Draw particles
            self.draw_particles()

            # Apply dark overlay
            self.screen.blit(dark_overlay, (0, 0))

            # Draw HUD
            self.draw_hud()

            # Update display
            pygame.display.flip()
            self.clock.tick(FPS)

            if self.game_won:
                self.display_level_completion()
                self.current_level += 1
                if self.current_level > self.max_levels:
                    print(f"Congratulations! You've completed all levels with a total score of {self.total_score}!")
                    running = False
                else:
                    self.setup_level()
                    self.light_engine = LightEngine(SCREEN_WIDTH, SCREEN_HEIGHT, darkness_level=self.current_level)
                    self.light_timer = 0
                    self.light_duration = max(10, 20 - (self.current_level * 2))  # Decrease light duration with each level
                    self.game_over = False
                    self.game_won = False

        pygame.quit()

def main():
    """Main game initialization"""
    game = EchoingDepthsGame()
    game.play()

if __name__ == "__main__":
    main()