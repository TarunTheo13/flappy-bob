import pygame
import json
import os
import random
from enum import Enum
from pathlib import Path

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Game Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

class GameState(Enum):
    START = 1
    PLAYING = 2
    GAME_OVER = 3

class FlappyBob:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Flappy Bob")
        self.clock = pygame.time.Clock()
        self.game_state = GameState.START
        self.load_assets()
        self.setup_game()

    def load_assets(self):
        # Load and scale images
        self.assets_dir = Path("assets")
        
        # Load and scale background
        bg_path = self.assets_dir / "images" / "background.png"
        self.background = pygame.image.load(str(bg_path))
        self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # Load and scale player sprite
        player_path = self.assets_dir / "images" / "FlappyBob.png"
        self.player_img = pygame.image.load(str(player_path))
        self.player_img = pygame.transform.scale(self.player_img, (70, 70))  # Increased from 50x50 to 70x70
        
        # Load and scale obstacle sprite
        pylon_path = self.assets_dir / "images" / "Pylon.png"
        original_pylon = pygame.image.load(str(pylon_path))
        original_width, original_height = original_pylon.get_size()
        
        # Scale pylons to screen height while maintaining width proportion
        desired_width = 100  # Decreased from 120 to 100
        self.pylon_img = pygame.transform.scale(original_pylon, (desired_width, SCREEN_HEIGHT))
        self.pylon_height = SCREEN_HEIGHT  # Store height for calculations

        # Load sounds
        self.flap_sound = pygame.mixer.Sound(str(self.assets_dir / "sounds" / "flap.mp3"))
        self.game_over_sound = pygame.mixer.Sound(str(self.assets_dir / "sounds" / "gameover.mp3"))
        pygame.mixer.music.load(str(self.assets_dir / "sounds" / "bg.mp3"))

    def setup_game(self):
        # Load game configuration
        self.load_config()
        
        # Initialize player position
        self.player_x = SCREEN_WIDTH // 4
        self.player_y = SCREEN_HEIGHT // 2
        self.player_velocity = 0
        
        # Initialize game variables
        self.score = 0
        self.high_score = self.load_high_score()
        
        # Initialize obstacles
        self.obstacles = []
        self.obstacle_timer = 0
        
        # Start background music
        pygame.mixer.music.play(-1)

    def load_config(self):
        config_path = Path("config.json")
        if not config_path.exists():
            self.create_default_config()
        
        with open(config_path) as f:
            self.config = json.load(f)

    def create_default_config(self):
        default_config = {
            "gravity": 0.5,
            "jump_strength": -8,
            "obstacle_speed": 3,
            "obstacle_gap": 200,
            "obstacle_interval": 2000,  # milliseconds
            "levels": [
                {
                    "name": "Easy",
                    "obstacle_speed": 2,
                    "obstacle_interval": 2500
                },
                {
                    "name": "Medium",
                    "obstacle_speed": 3,
                    "obstacle_interval": 2000
                },
                {
                    "name": "Hard",
                    "obstacle_speed": 4,
                    "obstacle_interval": 1500
                }
            ]
        }
        
        with open("config.json", "w") as f:
            json.dump(default_config, f, indent=4)
        
        self.config = default_config

    def load_high_score(self):
        try:
            with open("highscore.txt", "r") as f:
                return int(f.read())
        except:
            return 0

    def save_high_score(self):
        with open("highscore.txt", "w") as f:
            f.write(str(self.high_score))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 or \
               (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE):
                if self.game_state == GameState.START:
                    self.game_state = GameState.PLAYING
                elif self.game_state == GameState.PLAYING:
                    self.player_velocity = self.config["jump_strength"]
                    self.flap_sound.play()
                elif self.game_state == GameState.GAME_OVER:
                    self.setup_game()
                    self.game_state = GameState.START
        
        return True

    def update(self):
        if self.game_state == GameState.PLAYING:
            # Update player
            self.player_velocity += self.config["gravity"]
            self.player_y += self.player_velocity
            
            # Update obstacles
            current_time = pygame.time.get_ticks()
            if current_time - self.obstacle_timer > self.config["obstacle_interval"]:
                self.create_obstacle()
                self.obstacle_timer = current_time
            
            self.update_obstacles()
            
            # Check collisions
            if self.check_collisions():
                self.game_over()

    def create_obstacle(self):
        gap_y = random.randint(100, SCREEN_HEIGHT - 100 - self.config["obstacle_gap"])
        self.obstacles.append({
            "x": SCREEN_WIDTH,
            "top_height": gap_y,
            "passed": False
        })

    def update_obstacles(self):
        for obstacle in self.obstacles[:]:
            obstacle["x"] -= self.config["obstacle_speed"]
            
            # Score point when passing obstacle
            if not obstacle["passed"] and obstacle["x"] < self.player_x:
                obstacle["passed"] = True
                self.score += 1
                
            # Remove off-screen obstacles
            if obstacle["x"] < -80:  # obstacle width
                self.obstacles.remove(obstacle)

    def check_collisions(self):
        player_rect = pygame.Rect(self.player_x, self.player_y, 60, 60)  # Slightly smaller than visual size for forgiving collisions
        
        # Check screen boundaries
        if self.player_y < 0 or self.player_y > SCREEN_HEIGHT - 40:
            return True
        
        # Check obstacle collisions
        for obstacle in self.obstacles:
            # Top obstacle from top of screen to gap
            top_rect = pygame.Rect(obstacle["x"], 0, 100, obstacle["top_height"])
            # Bottom obstacle from gap to bottom of screen
            bottom_rect = pygame.Rect(
                obstacle["x"],
                obstacle["top_height"] + self.config["obstacle_gap"],
                100,
                SCREEN_HEIGHT - (obstacle["top_height"] + self.config["obstacle_gap"])
            )
            
            if player_rect.colliderect(top_rect) or player_rect.colliderect(bottom_rect):
                return True
        
        return False

    def game_over(self):
        self.game_state = GameState.GAME_OVER
        self.game_over_sound.play()
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score()

    def draw(self):
        # Draw background
        self.screen.blit(self.background, (0, 0))
        
        # Draw obstacles
        for obstacle in self.obstacles:
            # Top obstacle - clip it to the gap
            top_pylon = pygame.Surface((100, obstacle["top_height"]))
            top_pylon.blit(self.pylon_img, (0, 0))
            self.screen.blit(pygame.transform.flip(top_pylon, False, True), (obstacle["x"], 0))
            
            # Bottom obstacle - start from the gap
            bottom_height = SCREEN_HEIGHT - (obstacle["top_height"] + self.config["obstacle_gap"])
            bottom_pylon = pygame.Surface((100, bottom_height))
            bottom_pylon.blit(self.pylon_img, (0, 0))
            self.screen.blit(bottom_pylon, (obstacle["x"], obstacle["top_height"] + self.config["obstacle_gap"]))
        
        # Draw player
        self.screen.blit(self.player_img, (self.player_x, self.player_y))
        
        # Draw score
        font = pygame.font.Font(None, 36)
        score_text = font.render("Score: {}".format(self.score), True, BLACK)
        high_score_text = font.render("High Score: {}".format(self.high_score), True, BLACK)
        self.screen.blit(score_text, (10, 10))
        self.screen.blit(high_score_text, (10, 50))
        
        # Draw game state specific elements
        if self.game_state == GameState.START:
            start_text = font.render("Click or Press SPACE to Start", True, BLACK)
            text_rect = start_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
            self.screen.blit(start_text, text_rect)
        elif self.game_state == GameState.GAME_OVER:
            game_over_text = font.render("Game Over!", True, BLACK)
            restart_text = font.render("Click or Press SPACE to Restart", True, BLACK)
            game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 30))
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 30))
            self.screen.blit(game_over_text, game_over_rect)
            self.screen.blit(restart_text, restart_rect)
        
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()

if __name__ == "__main__":
    game = FlappyBob()
    game.run()
