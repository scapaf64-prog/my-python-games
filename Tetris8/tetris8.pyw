import pygame
import random
import os

BASE = os.path.dirname(os.path.abspath(__file__))

pygame.init()

pygame.mixer.init()

line_clear_sound = pygame.mixer.Sound(os.path.join(BASE, "laser-gun.mp3"))
line_fall_sound = pygame.mixer.Sound(os.path.join(BASE, "fall.mp3"))

# Screen settings
WIDTH, HEIGHT = 300, 600
BLOCK_SIZE = 30
COLS = WIDTH // BLOCK_SIZE
ROWS = HEIGHT // BLOCK_SIZE

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tetris")

clock = pygame.time.Clock()

clearing_lines = []
clear_alpha = 255
FADE_SPEED = 6

shake_timer = 0
# SHAKE_DURATION = 25
SHAKE_DURATION = 20
SHAKE_INTENSITY = 8


# Colors
BLACK = (0, 0, 0)
GRAY = (40, 40, 40)

COLORS = [
    (0, 255, 255),   # I
    (255, 255, 0),   # O
    (128, 0, 128),   # T
    (0, 255, 0),     # S
    (255, 0, 0),     # Z
    (0, 0, 255),     # J
    (255, 165, 0)    # L
]

# Tetromino shapes
SHAPES = [
    [[1, 1, 1, 1]],

    [[1, 1],
     [1, 1]],

    [[0, 1, 0],
     [1, 1, 1]],

    [[0, 1, 1],
     [1, 1, 0]],

    [[1, 1, 0],
     [0, 1, 1]],

    [[1, 0, 0],
     [1, 1, 1]],

    [[0, 0, 1],
     [1, 1, 1]]
]


class Piece:
    def __init__(self):
        self.shape = random.choice(SHAPES)
        self.color = COLORS[SHAPES.index(self.shape)]
        self.x = COLS // 2 - len(self.shape[0]) // 2
        self.y = 0

    def rotate(self):
        self.shape = [list(row) for row in zip(*self.shape[::-1])]


grid = [[BLACK for _ in range(COLS)] for _ in range(ROWS)]
current_piece = Piece()
score = 0


def valid_move(piece, dx=0, dy=0):
    for y, row in enumerate(piece.shape):
        for x, cell in enumerate(row):
            if cell:
                nx = piece.x + x + dx
                ny = piece.y + y + dy

                if nx < 0 or nx >= COLS or ny >= ROWS:
                    return False

                if ny >= 0 and grid[ny][nx] != BLACK:
                    return False
    return True


def merge_piece(piece):
    for y, row in enumerate(piece.shape):
        for x, cell in enumerate(row):
            if cell:
                grid[piece.y + y][piece.x + x] = piece.color


def check_lines():
    full_lines = []

    for y, row in enumerate(grid):
        if BLACK not in row:
            full_lines.append(y)

    return full_lines


def clear_lines(lines):
    global score, grid

    new_grid = [row for i, row in enumerate(grid) if i not in lines]

    for _ in lines:
        new_grid.insert(0, [BLACK for _ in range(COLS)])

    score += len(lines) * 100
    grid = new_grid


def draw_line_clear_animation():
    global clear_alpha

    fade_surface = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE))
    fade_surface.set_alpha(clear_alpha)

    for row in clearing_lines:
        for col in range(COLS):

            color = grid[row][col]

            if color != BLACK:
                fade_surface.fill(color)

                shake_x = 0

                if shake_timer > 0:
                    shake_x = random.randint(
                        -SHAKE_INTENSITY,
                        SHAKE_INTENSITY
                    )

                screen.blit(
                    fade_surface,
                    (
                        col * BLOCK_SIZE + shake_x,
                        row * BLOCK_SIZE
                    )
                )

                pygame.draw.rect(
                    screen,
                    GRAY,
                    (
                        col * BLOCK_SIZE + shake_x,
                        row * BLOCK_SIZE,
                        BLOCK_SIZE,
                        BLOCK_SIZE
                    ),
                    1
                )

def draw():
    screen.fill(BLACK)

    for y in range(ROWS):
        for x in range(COLS):

            if y in clearing_lines:
                continue

            pygame.draw.rect(
                screen,
                grid[y][x],
                (
                    x * BLOCK_SIZE,
                    y * BLOCK_SIZE,
                    BLOCK_SIZE,
                    BLOCK_SIZE
                )
            )

            pygame.draw.rect(
                screen,
                GRAY,
                (
                    x * BLOCK_SIZE,
                    y * BLOCK_SIZE,
                    BLOCK_SIZE,
                    BLOCK_SIZE
                ),
                1
            )

    if clearing_lines:
        draw_line_clear_animation()

    else:

        # Draw current piece
        for y, row in enumerate(current_piece.shape):
            for x, cell in enumerate(row):
                if cell:
                     rect = pygame.Rect(
                         (current_piece.x + x) * BLOCK_SIZE,
                         (current_piece.y + y) * BLOCK_SIZE,
                         BLOCK_SIZE,
                         BLOCK_SIZE
                     )

                     pygame.draw.rect(screen, current_piece.color, rect)
                     pygame.draw.rect(screen, GRAY, rect, 1)

    font = pygame.font.SysFont(None, 30)
    text = font.render(f"Score: {score}", True, (255, 255, 255))
    screen.blit(text, (10, 10))

    pygame.display.flip()

def game_over():
    #  print("Game Over!")
    font = pygame.font.SysFont(None, 60)
    text = font.render("GAME OVER", True, (255, 0, 0))

    screen.blit(
        text,
        (WIDTH // 2 - text.get_width() // 2,
         HEIGHT // 2 - text.get_height() // 2)
    )

    pygame.display.flip()
    pygame.time.wait(3000)


fall_time = 0
running = True

while running:
    dt = clock.tick(60)
    fall_time += dt

    if shake_timer > 0:
        shake_timer -= 1

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                running = False

            if event.key == pygame.K_LEFT:
                if valid_move(current_piece, dx=-1):
                    current_piece.x -= 1

            elif event.key == pygame.K_RIGHT:
                if valid_move(current_piece, dx=1):
                    current_piece.x += 1

            elif event.key == pygame.K_DOWN:
                if valid_move(current_piece, dy=1):
                    current_piece.y += 1

            elif event.key == pygame.K_UP:
                old_shape = [row[:] for row in current_piece.shape]
                current_piece.rotate()
                if not valid_move(current_piece):
                    current_piece.shape = old_shape

            elif event.key == pygame.K_SPACE:
               # Hard drop
               while valid_move(current_piece, dy=1):
                   current_piece.y += 1

               line_fall_sound.play()

               merge_piece(current_piece)
               lines = check_lines()

               if lines:
                   clearing_lines = lines
                   clear_alpha = 255
                   shake_timer = SHAKE_DURATION
                   line_clear_sound.play()
               else:
                   current_piece = Piece()

                   if not valid_move(current_piece):
                      game_over()
                      running = False

    if not clearing_lines:
        if fall_time > 500:
            fall_time = 0

            if valid_move(current_piece, dy=1):
                current_piece.y += 1
            else:
                merge_piece(current_piece)
                lines = check_lines()

                if lines:
                    clearing_lines = lines
                    clear_alpha = 255
                    shake_timer = SHAKE_DURATION
                    line_clear_sound.play()
                else:
                   current_piece = Piece()

                   if not valid_move(current_piece):
                      game_over()
                      running = False

    if clearing_lines:
        clear_alpha -= FADE_SPEED

        if clear_alpha <= 0:

            clear_lines(clearing_lines)

            clearing_lines = []
            clear_alpha = 255

            current_piece = Piece()

            if not valid_move(current_piece):
                game_over()
                running = False

    draw()

pygame.quit()