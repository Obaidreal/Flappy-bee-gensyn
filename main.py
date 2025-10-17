import pygame
import random
import sys
import asyncio
from PIL import Image
import io
import os
# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
GRAVITY = 0.5
JUMP_STRENGTH = -8
PIPE_WIDTH = 60
PIPE_GAP = 200
PIPE_SPEED = 3
FPS = 60

# Colors (Gensyn AI theme)
BLACK = (35, 8, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
Pink = (250, 215, 209)

# Set up display (Pygbag handles this for web)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Flappy Bee: Gensyn AI Edition")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)

# Detect web environment (Pygbag sets PYGBAG)
IS_WEB = 'PYGBAG' in os.environ

# Cloud API endpoint (set in Vercel environment variables, default for local testing)
CLOUD_UPLOAD_URL = os.environ.get('CLOUD_UPLOAD_URL', 'https://flappy-bee-api.vercel.app/api/highscore')  # Default for local testing

# Load and process animated GIF
def load_gif_frames(gif_path):
    try:
        gif = Image.open(gif_path)
        frames = []
        durations = []
        for frame in range(gif.n_frames):
            gif.seek(frame)
            frame_image = gif.convert('RGBA')
            frame_data = frame_image.tobytes()
            pygame_frame = pygame.image.fromstring(frame_data, frame_image.size, 'RGBA')
            pygame_frame = pygame.transform.scale(pygame_frame, (100, 100))
            frames.append(pygame_frame)
            duration = gif.info.get('duration', 100)
            durations.append(duration / 1000.0)
        return frames, durations
    except Exception as e:
        print(f"Error loading GIF: {e}")
        placeholder = pygame.Surface((100, 100), pygame.SRCALPHA)
        placeholder.fill((255, 0, 0))
        return [placeholder], [0.1]

# Load GIF frames
gif_frames, frame_durations = load_gif_frames("./logo.gif")

# Load and scale bee image
bee_image = pygame.image.load("./bee.png")
bee_image = pygame.transform.scale(bee_image, (40, 40))

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
        image_rect = bee_image.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(bee_image, image_rect)

    def get_rect(self):
        return pygame.Rect(self.x - 20, self.y - 20, 40, 40)

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
        pygame.draw.rect(screen, Pink, (self.x, 0, PIPE_WIDTH, 20))
        pygame.draw.rect(screen, WHITE, self.bottom_rect)
        pygame.draw.rect(screen, Pink, (self.x, self.bottom_rect.y - 20, PIPE_WIDTH, 20))

def draw_text(screen, text, font, color, x, y):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(x, y))
    screen.blit(text_surface, text_rect)

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
        draw_text(screen, name + "_", font, Pink, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        draw_text(screen, "Press ENTER to submit", small_font, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50)
        pygame.display.flip()
        clock.tick(FPS)
    return name if name else "Anonymous"

# Function to fetch cloud high score
def fetch_cloud_highscore():
    if IS_WEB and CLOUD_UPLOAD_URL:
        try:
            import js
            result = js.eval(f"""
                fetch('{CLOUD_UPLOAD_URL}', {{ method: 'GET' }})
                 .then(response => response.json())
                 .then(data => {{ return {{ name: data.name || 'Anonymous', score: data.score || 0 }}; }})
                 .catch(error => {{ console.error('Error fetching high score:', error); return {{ name: 'Anonymous', score: 0 }}; }});
            """)
            return result['name'], result['score']
        except Exception as e:
            print(f"JavaScript interop error: {e}")
            return "Anonymous", 0
    return "Anonymous", 0

# Function to submit score to cloud (web-only)
def submit_score_to_cloud(name, score):
    if IS_WEB and CLOUD_UPLOAD_URL:
        try:
            import js
            js.eval(f"""
                fetch('{CLOUD_UPLOAD_URL}', {
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ name: '{name}', score: {score} }})
                }).then(response => response.json())
                 .then(data => console.log('Score submitted:', data))
                 .catch(error => console.error('Error submitting score:', error));
            """)
        except Exception as e:
            print(f"JavaScript interop error: {e}")

async def main():
    bee = Bee()
    pipes = [Pipe(SCREEN_WIDTH + 100)]
    score = 0
    running = True
    game_over = False
    # Fetch initial cloud high score
    cloud_highscore_name, cloud_highscore = fetch_cloud_highscore()
    highscore = cloud_highscore  # Use cloud high score as baseline
    player_name = None
    start_screen = True
    current_frame = 0
    frame_timer = 0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if start_screen:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    start_screen = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    start_screen = False
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                if not game_over:
                    bee.jump()
                else:
                    bee = Bee()
                    pipes = [Pipe(SCREEN_WIDTH + 100)]
                    score = 0
                    game_over = False
                    player_name = None

        if not start_screen and not game_over:
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

            if bee.y - bee.radius < 0 or bee.y + bee.radius > SCREEN_HEIGHT:
                game_over = True
            for pipe in pipes:
                if bee.get_rect().colliderect(pipe.top_rect) or bee.get_rect().colliderect(pipe.bottom_rect):
                    game_over = True

        if game_over and player_name is None:
            player_name = get_player_name(screen, font)
            if score > highscore:  # Compare with cloud high score
                highscore = score
                if IS_WEB and CLOUD_UPLOAD_URL:  # Submit to cloud if higher than cloud high score
                    submit_score_to_cloud(player_name, score)

        screen.fill(BLACK)
        if start_screen:
            frame_timer += 1 / FPS
            if frame_timer >= frame_durations[current_frame]:
                current_frame = (current_frame + 1) % len(gif_frames)
                frame_timer = 0
            frame_rect = gif_frames[current_frame].get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
            screen.blit(gif_frames[current_frame], frame_rect)
            draw_text(screen, "Flappy Bee: Gensyn AI Edition", font, Pink, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)
            draw_text(screen, "Tap the screen or press SPACE to start!", small_font, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            draw_text(screen, "Powered by boogyman", small_font, Pink, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30)
            draw_text(screen, "@gensynai", small_font, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60)
        else:
            bee.draw(screen)
            for pipe in pipes:
                pipe.draw(screen)
            draw_text(screen, f"Models Trained: {score}", font, WHITE, SCREEN_WIDTH // 2, 50)
            draw_text(screen, f"High Score: {highscore} by {player_name if player_name else cloud_highscore_name}", small_font, WHITE, SCREEN_WIDTH // 2, 80)

            if game_over:
                draw_text(screen, "Game Over!", font, YELLOW, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)
                draw_text(screen, f"Final Score: {score}", small_font, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
                draw_text(screen, "Powered by boogyman", small_font, Pink, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30)
                draw_text(screen, "@gensynai", small_font, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60)
                draw_text(screen, "Tap screen or press SPACE to restart", small_font, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50)
            else:
                draw_text(screen, "Tap screen or press SPACE to flap!", small_font, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30)

        pygame.display.flip()
        await asyncio.sleep(0)
        clock.tick(FPS)

if __name__ == "__main__":
    asyncio.run(main())
    pygame.quit()
    sys.exit()
