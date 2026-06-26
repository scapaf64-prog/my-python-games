import pygame
import random

# -----------------------------
# CONFIG
# -----------------------------
WIDTH = 300
HEIGHT = 600
BLOCK_SIZE = 30

GRID_W = WIDTH // BLOCK_SIZE
GRID_H = HEIGHT // BLOCK_SIZE

FPS = 60

BLACK = (10, 10, 20)
GRAY = (40, 40, 50)
WHITE = (255, 255, 255)

SHAPES = [
    [[1, 1, 1, 1]],

    [[1, 1],
     [1, 1]],

    [[0, 1, 0],
     [1, 1, 1]],

    [[1, 0, 0],
     [1, 1, 1]],

    [[0, 0, 1],
     [1, 1, 1]],

    [[0, 1, 1],
     [1, 1, 0]],

    [[1, 1, 0],
     [0, 1, 1]],
]

COLORS = [
    (0, 255, 255),
    (255, 255, 0),
    (180, 0, 255),
    (255, 120, 0),
    (0, 100, 255),
    (0, 255, 0),
    (255, 0, 0),
]


# -----------------------------
# LIGHTNING
# -----------------------------
def lightning_points(start, end, displacement):
    points = [start, end]

    while displacement > 2:
        new_points = [points[0]]

        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]

            mx = (x1 + x2) / 2
            my = (y1 + y2) / 2 + random.uniform(
                -displacement,
                displacement
            )

            new_points.append((mx, my))
            new_points.append((x2, y2))

        points = new_points
        displacement *= 0.5

    return points


def draw_lightning(screen, row):
    center_y = row * BLOCK_SIZE + BLOCK_SIZE // 2

    pts = lightning_points(
        (0, center_y),
        (WIDTH, center_y),
        40
    )

    pygame.draw.lines(screen, (0, 100, 255), False, pts, 12)
    pygame.draw.lines(screen, (0, 200, 255), False, pts, 8)
    pygame.draw.lines(screen, (255, 255, 255), False, pts, 3)


# -----------------------------
# PIECE
# -----------------------------
class Piece:
    def __init__(self):
        idx = random.randrange(len(SHAPES))
        self.shape = SHAPES[idx]
        self.color = COLORS[idx]

        self.x = GRID_W // 2 - len(self.shape[0]) // 2
        self.y = 0

    def rotate(self):
        self.shape = [
            list(row)
            for row in zip(*self.shape[::-1])
        ]


# -----------------------------
# GAME
# -----------------------------
class Tetris:
    def __init__(self):
        self.grid = [
            [None for _ in range(GRID_W)]
            for _ in range(GRID_H)
        ]

        self.current = Piece()

        self.game_over = False
        if not self.valid(self.current):
            self.game_over = True

        self.fall_timer = 0
        self.fall_speed = 500

        self.score = 0

        self.clearing_rows = []
        self.clear_timer = 0

    def valid(self, piece):
        for y, row in enumerate(piece.shape):
            for x, cell in enumerate(row):

                if not cell:
                    continue

                gx = piece.x + x
                gy = piece.y + y

                if gx < 0 or gx >= GRID_W:
                    return False

                if gy >= GRID_H:
                    return False

                if gy >= 0 and self.grid[gy][gx]:
                    return False

        return True

    def lock_piece(self):
        p = self.current

        for y, row in enumerate(p.shape):
            for x, cell in enumerate(row):

                if cell:
                    gx = p.x + x
                    gy = p.y + y

                    if gy >= 0:
                        self.grid[gy][gx] = p.color

        self.find_lines()

        if not self.clearing_rows:
            self.current = Piece()

            if not self.valid(self.current):
                self.game_over = True

    def find_lines(self):
        rows = []

        for y in range(GRID_H):
            if all(self.grid[y]):
                rows.append(y)

        if rows:
            self.clearing_rows = rows
            self.clear_timer = pygame.time.get_ticks()
            line_clear_sound.play()

    def remove_lines(self):
#         for row in sorted(self.clearing_rows, reverse=True):
        for row in sorted(self.clearing_rows):
            del self.grid[row]
            self.grid.insert(
                0,
                [None for _ in range(GRID_W)]
            )

        self.score += len(self.clearing_rows) * 100

        self.clearing_rows = []
        self.current = Piece()

        if not self.valid(self.current):
            self.game_over = True

    def move(self, dx):
        self.current.x += dx

        if not self.valid(self.current):
            self.current.x -= dx

    def rotate(self):
        old = [r[:] for r in self.current.shape]

        self.current.rotate()

        if not self.valid(self.current):
            self.current.shape = old

    def drop(self):
        self.current.y += 1

        if not self.valid(self.current):
            self.current.y -= 1
            self.lock_piece()

    def update(self):
        if self.clearing_rows:

            if pygame.time.get_ticks() - self.clear_timer > 500:
                self.remove_lines()

            return

        now = pygame.time.get_ticks()

        if now - self.fall_timer > self.fall_speed:
            self.fall_timer = now
            self.drop()

    def draw(self, screen):

        screen.fill(BLACK)

        # grid
        for y in range(GRID_H):
            for x in range(GRID_W):

                rect = pygame.Rect(
                    x * BLOCK_SIZE,
                    y * BLOCK_SIZE,
                    BLOCK_SIZE,
                    BLOCK_SIZE
                )

                pygame.draw.rect(
                    screen,
                    GRAY,
                    rect,
                    1
                )

                color = self.grid[y][x]

                if color:
                    pygame.draw.rect(
                        screen,
                        color,
                        rect.inflate(-2, -2)
                    )

        # current piece
        if not self.clearing_rows:
            p = self.current

            for y, row in enumerate(p.shape):
                for x, cell in enumerate(row):

                    if cell:

                        rect = pygame.Rect(
                            (p.x + x) * BLOCK_SIZE,
                            (p.y + y) * BLOCK_SIZE,
                            BLOCK_SIZE,
                            BLOCK_SIZE
                        )

                        pygame.draw.rect(
                            screen,
                            p.color,
                            rect.inflate(-2, -2)
                        )
        # lightning effect
        for row in self.clearing_rows:
            draw_lightning(screen, row)

        font = pygame.font.SysFont(None, 32)

        text = font.render(
            f"Score: {self.score}",
            True,
            WHITE
        )

        screen.blit(text, (10, 10))


# -----------------------------
# MAIN
# -----------------------------
pygame.init()
pygame.mixer.init()

line_clear_sound = pygame.mixer.Sound("electricity.mp3")
line_fall_sound = pygame.mixer.Sound("fall.mp3")

screen = pygame.display.set_mode(
    (WIDTH, HEIGHT)
)

pygame.display.set_caption(
    "Lightning Tetris"
)

clock = pygame.time.Clock()

game = Tetris()

running = True

while running:

    if game.game_over:
        running = False

    dt = clock.tick(FPS)

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            if game.clearing_rows:
                continue

            if event.key == pygame.K_ESCAPE:
                running = False

            if event.key == pygame.K_LEFT:
                game.move(-1)

            elif event.key == pygame.K_RIGHT:
                game.move(1)

            elif event.key == pygame.K_UP:
                game.rotate()

            elif event.key == pygame.K_DOWN:
                game.drop()

            elif event.key == pygame.K_SPACE:

                line_fall_sound.play()
                while game.valid(game.current):
                    game.current.y += 1

                game.current.y -= 1
                game.lock_piece()

    game.update()
    game.draw(screen)

    pygame.display.flip()

pygame.quit()