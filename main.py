import pygame
import random
import sys
import asyncio
import json
import os
import requests  # For API calls

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
GRAVITY = 0.4
JUMP_STRENGTH = -8
PIPE_WIDTH = 60
PIPE_GAP = 200
PIPE_SPEED = 3
FPS = 60

# Colors (Gensyn AI theme)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
BLUE = (0, 150, 255)

# Set up display (Pygbag handles this for web)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Flappy Bee: Gensyn AI Edition")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)

# API endpoint (update to your Vercel URL after deploy)
API_BASE = os.environ.get('API_BASE', 'http://localhost:8000')  # Fallback for local testing

class Bee:
    def __init__(self):
        self.x = 50
        self.y = SCREEN_HEIGHT // 2
        self.velocity = 0
        self.radius = 20

    def jump(self):
        self.velocity = JUMP_STRENGTH

    def update(self):
        self.velocity += GRAVITY
        self.y += self.velocity

    def draw(self, screen):
        pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), self.radius)
        pygame.draw.line(screen, WHITE, (self.x - 15, self.y - 5), (self.x - 25, self.y - 15), 3)
        pygame.draw.line(screen, WHITE, (self.x - 15, self.y + 5), (self.x - 25, self.y + 15), 3)

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

class Pipe:
    def __init__(self, x):
        self.x = x
        self.height = random.randint(100, SCREEN_HEIGHT - PIPE_GAP - 100)
        self.top_rect = pygame.Rect(self.x, 0, PIPE_WIDTH, self.height)
        self.bottom_rect = pygame.Rect(self.x, self.height + PIPE_GAP, PIPE_WIDTH, SCREEN_HEIGHT - self.height - PIPE_GAP)
        self.passed = False

    def update(self):
        self.x -= PIPE_SPEED
        self.top_rect.x = self.x
        self.bottom_rect.x = self.x

    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, self.top_rect)
        pygame.draw.rect(screen, BLUE, (self.x, 0, PIPE_WIDTH, 20))
        pygame.draw.rect(screen, WHITE, self.bottom_rect)
        pygame.draw.rect(screen, BLUE, (self.x, self.bottom_rect.y - 20, PIPE_WIDTH, 20))

def draw_text(screen, text, font, color, x, y):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(x, y))
    screen.blit(text_surface, text_rect)

def load_highscore():
    try:
        response = requests.get(f"{API_BASE}/api/highscore", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('name', 'Anonymous'), data.get('score', 0)
    except:
        pass  # Fallback to local
    # Local fallback
    if os.path.exists("highscore.txt"):
        try:
            with open("highscore.txt", "r") as f:
                data = json.load(f)
                return data.get("name", "Anonymous"), data.get("score", 0)
        except:
            pass
    return "Anonymous", 0

def save_highscore(name, score):
    try:
        response = requests.post(f"{API_BASE}/api/highscore", json={'name': name, 'score': score}, timeout=5)
        if response.status_code == 200:
            return
    except:
        pass  # Fallback to local
    # Local fallback
    with open("highscore.txt", "w") as f:
        json.dump({"name": name, "score": score}, f)

def get_player_name(screen, font):
    name = ""
    input_active = True
    while input_active:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and name:
                    input_active = False
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                elif len(name) < 15:
                    name += event.unicode if event.unicode.isalnum() else ""
        screen.fill(BLACK)
        draw_text(screen, "Enter Your Name:", font, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)
        draw_text(screen, name + "_", font, BLUE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)  # Cursor
        draw_text(screen, "Press ENTER to submit", small_font, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50)
        pygame.display.flip()
        clock.tick(FPS)
    return name if name else "Anonymous"

async def main():
    bee = Bee()
    pipes = [Pipe(SCREEN_WIDTH + 100)]
    score = 0
    running = True
    game_over = False
    highscore_name, highscore = load_highscore()
    player_name = None

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if not game_over:
                        bee.jump()
                    else:
                        bee = Bee()
                        pipes = [Pipe(SCREEN_WIDTH + 100)]
                        score = 0
                        game_over = False
                        player_name = None

        if not game_over:
            bee.update()

            if pipes[-1].x < SCREEN_WIDTH - 200:
                pipes.append(Pipe(SCREEN_WIDTH))

            for pipe in pipes[:]:
                pipe.update()
                if pipe.x + PIPE_WIDTH < 0:
                    pipes.remove(pipe)
                if not pipe.passed and pipe.x + PIPE_WIDTH < bee.x:
                    pipe.passed = True
                    score += 1

            # Collisions
            if bee.y - bee.radius < 0 or bee.y + bee.radius > SCREEN_HEIGHT:
                game_over = True
            for pipe in pipes:
                if bee.get_rect().colliderect(pipe.top_rect) or bee.get_rect().colliderect(pipe.bottom_rect):
                    game_over = True

        if game_over and player_name is None:
            player_name = get_player_name(screen, font)
            if score > highscore:
                highscore = score
                highscore_name = player_name
                save_highscore(highscore_name, highscore)

        # Draw
        screen.fill(BLACK)
        bee.draw(screen)
        for pipe in pipes:
            pipe.draw(screen)

        draw_text(screen, f"Models Trained: {score}", font, WHITE, SCREEN_WIDTH // 2, 50)
        draw_text(screen, f"High Score: {highscore} by {highscore_name}", small_font, WHITE, SCREEN_WIDTH // 2, 80)

        if game_over:
            draw_text(screen, "Game Over!", font, BLUE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)
            draw_text(screen, f"Final Score: {score}", small_font, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            draw_text(screen, "Powered by Gensyn AI", small_font, BLUE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30)
            draw_text(screen, "@gensynai - Train AI on the blockchain!", small_font, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60)
            draw_text(screen, "Press SPACE to restart", small_font, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50)
        else:
            draw_text(screen, "Tap SPACE to flap!", small_font, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30)

        pygame.display.flip()
        await asyncio.sleep(0)  # Yield for browser
        clock.tick(FPS)

if __name__ == "__main__":
    asyncio.run(main())
    pygame.quit()
    sys.exit()
