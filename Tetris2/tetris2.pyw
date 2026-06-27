
import pygame, math
import random

colors = [
    (0, 0, 0),
    (120, 37, 179),
    (100, 179, 179),
    (80, 34, 22),
    (80, 134, 22),
    (180, 34, 22),
    (180, 34, 122),
]


class Figure:
    x = 0
    y = 0

    figures = [
        [[1, 5, 9, 13], [4, 5, 6, 7]],
        [[4, 5, 9, 10], [2, 6, 5, 9]],
        [[6, 7, 9, 10], [1, 5, 6, 10]],
        [[1, 2, 5, 9], [0, 4, 5, 6], [1, 5, 9, 8], [4, 5, 6, 10]],
        [[1, 2, 6, 10], [5, 6, 7, 9], [2, 6, 10, 11], [3, 5, 6, 7]],
        [[1, 4, 5, 6], [1, 4, 5, 9], [4, 5, 6, 9], [1, 5, 6, 9]],
        [[1, 2, 5, 6]],
    ]

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.type = random.randint(0, len(self.figures) - 1)
        self.color = random.randint(1, len(colors) - 1)
        self.rotation = 0

    def image(self):
        return self.figures[self.type][self.rotation]

    def rotate(self):
        self.rotation = (self.rotation + 1) % len(self.figures[self.type])


class Tetris:

    def __init__(self, height, width):
        self.level = 2
        self.score = 0
        self.state = "start"
        self.field = []
        self.x = 100
        self.y = 60
        self.zoom = 20
        self.figure = None
        self.height = height
        self.width = width
        self.fall_sound = pygame.mixer.Sound("fall.ogg")
        self.clear_sound = pygame.mixer.Sound("clear.ogg")
        self.line = []

        for i in range(height):
            self.line.append(0)

        for i in range(height):
            new_line = []
            for j in range(width):
                new_line.append(0)
            self.field.append(new_line)

    def new_figure(self):
        self.figure = Figure(3, 0)

    def intersects(self):
        intersection = False
        for i in range(4):
            for j in range(4):
                if i * 4 + j in self.figure.image():
                    if i + self.figure.y > self.height - 1 or \
                            j + self.figure.x > self.width - 1 or \
                            j + self.figure.x < 0 or \
                            self.field[i + self.figure.y][j + self.figure.x] > 0:
                        intersection = True
        return intersection

    def break_lines(self):
        lines = 0
        self.line[0] = 0
        for i in range(1, self.height):
            zeros = 0
            self.line[i] = 0
            for j in range(self.width):
                if self.field[i][j] == 0:
                    zeros += 1
            if zeros == 0:
                lines += 1
                self.line[i] = i
                for i1 in range(i, 1, -1):
                    for j in range(self.width):
                        self.field[i1][j] = self.field[i1 - 1][j]

                self.clear_sound.play()

        self.score += lines ** 2

    def go_space(self):
        while not self.intersects():
            self.figure.y += 1
        self.figure.y -= 1

        self.fall_sound.play()

        self.freeze()

    def go_down(self):  
        self.figure.y += 1
        if self.intersects():
            self.figure.y -= 1
            self.freeze()

    def freeze(self):
        for i in range(4):
            for j in range(4):
                if i * 4 + j in self.figure.image():
                    self.field[i + self.figure.y][j + self.figure.x] = self.figure.color
        self.break_lines()
        self.new_figure()
        if self.intersects():
            self.state = "gameover"

    def go_side(self, dx):
        old_x = self.figure.x
        self.figure.x += dx
        if self.intersects():
            self.figure.x = old_x

    def rotate(self):
        old_rotation = self.figure.rotation
        self.figure.rotate()
        if self.intersects():
            self.figure.rotation = old_rotation


# Initialize the game engine
pygame.init()

# Define some colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GRAY = (240,240,240)

size = (400, 500)
screen = pygame.display.set_mode(size)

pygame.display.set_caption("Tetris")

# Loop until the user clicks the close button.
done = False
clock = pygame.time.Clock()
fps = 200
game = Tetris(20, 10)
counter = 0

pressing_down = False

NEON = (0, 255, 200)

def draw_neon_rect(surface, rect, color, thickness=4, glow_size=12):
    for i in range(glow_size, 0, -1):
        alpha = max(10, 255 // (i * 2))
        glow_color = (*color, alpha)

        glow_surf = pygame.Surface(
            (rect.width + i*4, rect.height + i*4),
            pygame.SRCALPHA
        )
        pygame.draw.rect(glow_surf, glow_color, glow_surf.get_rect(), border_radius=8)
        surface.blit(glow_surf, (rect.x - i*2, rect.y - i*2))

    pygame.draw.rect(surface, color, rect, thickness, border_radius=8)


while not done:
    if game.figure is None:
        game.new_figure()
    counter += 1
    if counter > 100000:
        counter = 0

    score_alt = game.score

    if counter % (fps // game.level // 2) == 0 or pressing_down:
        if game.state == "start":
            game.go_down()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                game.rotate()
            if event.key == pygame.K_DOWN:
#                pressing_down = True
                game.go_down()
            if event.key == pygame.K_LEFT:
                game.go_side(-1)
            if event.key == pygame.K_RIGHT:
                game.go_side(1)
            if event.key == pygame.K_SPACE:
                game.go_space()
            if event.key == pygame.K_ESCAPE:
#                game.__init__(20, 10)
                done = True

    if event.type == pygame.KEYUP:
            if event.key == pygame.K_DOWN:
                pressing_down = False

    screen.fill(WHITE)

    for i in range(game.height):
        for j in range(game.width):
            pygame.draw.rect(screen, GRAY, [game.x + game.zoom * j, game.y + game.zoom * i, game.zoom, game.zoom], 1)
            if game.field[i][j] > 0:
                pygame.draw.rect(screen, colors[game.field[i][j]],
                                 [game.x + game.zoom * j + 1, game.y + game.zoom * i + 1, game.zoom - 2, game.zoom - 1])

    if game.figure is not None:
        for i in range(4):
            for j in range(4):
                p = i * 4 + j
                if p in game.figure.image():
                    pygame.draw.rect(screen, colors[game.figure.color],
                                     [game.x + game.zoom * (j + game.figure.x) + 1,
                                      game.y + game.zoom * (i + game.figure.y) + 1,
                                      game.zoom - 2, game.zoom - 2])

    if game.score > score_alt:
        for j in range(1, game.height):
            if game.line[j] > 0:

                r1 = game.x
                r2 = game.y + game.zoom * (game.line[j])
                r3 = game.zoom * 10
                r4 = game.zoom

                for k in range(1, 4):
                     if (j + k) < game.height:
                        if game.line[j+k] > 0:
                            r4 += game.zoom
                            game.line[j+k] = 0

                rect = pygame.Rect(r1, r2, r3, r4)

                pulse_time = 0
                pulse_duration = 35   # frames for full pulse
                pulse_done = False

                running = True
                while running:

                    screen.fill((5, 5, 10))
 
                    # Pulse only once
                    if not pulse_done:
                        pulse_time += 1
                        t = pulse_time / pulse_duration
                        if t >= 1:
                            t = 1
                            pulse_done = True

                        # Smooth pulse curve (ease in/out)
                        scale = 1 + math.sin(t * math.pi) * 0.1
                    else:
                        scale = 1  # no more pulsing
                        running = False

                    # Apply scale
                    pr = rect.copy()
                    pr.inflate_ip(rect.width * (scale - 1), rect.height * (scale - 1))

                    draw_neon_rect(screen, pr, NEON)

                    pygame.display.flip()
                    clock.tick(200)

    font = pygame.font.SysFont('Calibri', 25, True, False)
    font1 = pygame.font.SysFont('Calibri', 65, True, False)
    text = font.render("Score: " + str(game.score), True, BLACK)
    text_game_over = font1.render("Game Over", True, (255, 125, 0))
    text_game_over1 = font1.render("Press ESC", True, (255, 215, 0))

    screen.blit(text, [0, 0])
    if game.state == "gameover":
        screen.blit(text_game_over, [20, 200])
        screen.blit(text_game_over1, [20, 265])

    pygame.display.flip()
    clock.tick(fps)

pygame.quit()

