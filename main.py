import pygame
import numpy as np
import math
from noise import pnoise2
import random

# Screen and Game Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 700
SCREEN_TITLE = "Echoing Depths: Sound-Navigated Maze Survival"
GRID_SIZE = 50
MOVEMENT_SPEED = 3
FPS = 60

# Color Constants
WALL_COLOR = (50, 50, 50)
PLAYER_COLOR = (255, 255, 255)
EXIT_COLOR = (0, 255, 0)
BACKGROUND_COLOR = (0, 0, 0)

class MazeGenerator:
    @staticmethod
    def generate_maze(width, height):
        """Generate a simplified maze with guaranteed paths"""
        # Create a grid filled with walls
        maze = [['#' for _ in range(width)] for _ in range(height)]
        
        def in_bounds(x, y):
            return 0 <= x < width and 0 <= y < height
        
        def carve_passages(x, y):
            # Carve out passages
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            random.shuffle(directions)
            
            for dx, dy in directions:
                nx, ny = x + dx*2, y + dy*2
                if in_bounds(nx, ny) and maze[ny][nx] == '#':
                    maze[y+dy][x+dx] = ' '
                    maze[ny][nx] = ' '
                    carve_passages(nx, ny)
        
        # Start carving from the top left
        maze[1][1] = 'P'  # Player start
        carve_passages(1, 1)
        
        # Place exit
        maze[height-2][width-2] = 'E'
        
        return [''.join(row) for row in maze]

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
        
        # Initialize level
        self.setup_level()
    
    def setup_level(self):
        """Initialize a new game level"""
        # Generate maze with more open spaces
        maze = MazeGenerator.generate_maze(width=24, height=18)
        self.wall_list = []
        
        # Print maze for debugging
        for row in maze:
            print(row)
        
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
                    print(f"Player Start: {self.player_pos}")
                
                elif cell == 'E':
                    # Exit position
                    self.exit_pos = pygame.Vector2(
                        x + GRID_SIZE // 2, 
                        y + GRID_SIZE // 2
                    )
                    print(f"Exit Position: {self.exit_pos}")
    
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
            
            # Clear screen
            self.screen.fill(BACKGROUND_COLOR)
            
            # Handle player movement
            self.handle_movement()
            
            # Draw walls
            for wall in self.wall_list:
                pygame.draw.rect(self.screen, WALL_COLOR, wall)
            
            # Draw player
            pygame.draw.rect(self.screen, PLAYER_COLOR, 
                             pygame.Rect(self.player_pos.x - GRID_SIZE//4, 
                                         self.player_pos.y - GRID_SIZE//4, 
                                         GRID_SIZE//2, 
                                         GRID_SIZE//2))
            
            # Draw exit
            pygame.draw.rect(self.screen, EXIT_COLOR, 
                             pygame.Rect(self.exit_pos.x - GRID_SIZE//4, 
                                         self.exit_pos.y - GRID_SIZE//4, 
                                         GRID_SIZE//2, 
                                         GRID_SIZE//2))
            
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