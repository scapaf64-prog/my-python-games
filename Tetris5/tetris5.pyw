import pygame
import random
import os

BASE = os.path.dirname(os.path.abspath(__file__))

# Initialisierung
pygame.init()
pygame.mixer.init()

line_clear_sound = pygame.mixer.Sound(os.path.join(BASE, "whoosh.mp3"))
line_clear_sound.set_volume(0.2)
line_fall_sound = pygame.mixer.Sound(os.path.join(BASE, "fall.ogg"))
line_fall_sound.set_volume(0.5)

# Konstanten
BLOCK_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
GROW = 12
SHRINK = 18
MAX_SCALE = 1.6
DELAY = 2

SIDE_MARGIN = BLOCK_SIZE * 6   # gleich breit wie die rechte Seitenleiste

SCREEN_WIDTH = BLOCK_SIZE * (GRID_WIDTH + 12)
SCREEN_HEIGHT = BLOCK_SIZE * GRID_HEIGHT

# Farben
COLORS = [
    (0, 0, 0),        # Schwarz (Hintergrund)
    (0, 240, 240),    # Cyan (I)
    (240, 240, 0),    # Gelb (O)
    (160, 0, 240),    # Lila (T)
    (0, 240, 0),      # Grün (S)
    (240, 0, 0),      # Rot (Z)
    (0, 0, 240),      # Blau (J)
    (240, 160, 0),    # Orange (L)
]

# Tetromino-Formen
SHAPES = [
    [[1, 1, 1, 1]],                              # I
    [[2, 2], [2, 2]],                            # O
    [[0, 3, 0], [3, 3, 3]],                      # T
    [[0, 4, 4], [4, 4, 0]],                      # S
    [[5, 5, 0], [0, 5, 5]],                      # Z
    [[6, 0, 0], [6, 6, 6]],                      # J
    [[0, 0, 7], [7, 7, 7]],                      # L
]

class Tetris:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Tetris")
        self.clock = pygame.time.Clock()
        self.reset_game()

    def reset_game(self):
        self.grid = [[0] * GRID_WIDTH for _ in range(GRID_HEIGHT)]
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.game_over = False
        self.state = "PLAY"
        self.lines_to_clear = []
        self.current_line = None
        self.lines_cleared_pending = 0
        self.animation_timer = 0
        self.current_piece = self.new_piece()
        self.next_piece = self.new_piece()
        self.font = pygame.font.SysFont("arial", 24, bold=True)
        self.font_large = pygame.font.SysFont("arial", 52, bold=True)
        self.anim_t = 0

    def new_piece(self):
        shape = random.choice(SHAPES)
        return {
            'shape': [row[:] for row in shape],
            'x': GRID_WIDTH // 2 - len(shape[0]) // 2,
            'y': 0
        }

    def rotate(self, shape):
        return [list(row) for row in zip(*shape[::-1])]

    def valid_position(self, shape, offset_x, offset_y):
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    new_x = offset_x + x
                    new_y = offset_y + y
                    if new_x < 0 or new_x >= GRID_WIDTH or new_y >= GRID_HEIGHT:
                        return False
                    if new_y >= 0 and self.grid[new_y][new_x]:
                        return False
        return True

    def lock_piece(self):
        shape = self.current_piece['shape']
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    grid_y = self.current_piece['y'] + y
                    grid_x = self.current_piece['x'] + x
                    if grid_y >= 0:
                        self.grid[grid_y][grid_x] = cell

        self.clear_lines()

    def clear_lines(self):

        self.lines_to_clear = []

        for y in range(GRID_HEIGHT):
            if all(self.grid[y]):
                self.lines_to_clear.append(y)

        # von unten nach oben löschen
        self.lines_cleared_pending = len(self.lines_to_clear)

        if self.lines_to_clear:

            self.current_line = self.lines_to_clear.pop(0)

            self.anim_t = 0
            self.animation_timer = 0
            self.state = "ANIMATION"

            return

        else:

            # keine Animation nötig
            self.current_piece = self.next_piece
            self.next_piece = self.new_piece()

            if not self.valid_position(
                    self.current_piece["shape"],
                    self.current_piece["x"],
                    self.current_piece["y"]):
                self.game_over = True

    def update_animation(self, dt):

        self.animation_timer += dt
        self.anim_t += 1

        # Sound nur einmal pro Zeile
        if self.animation_timer == dt:
            line_clear_sound.play()

        if self.animation_timer < 500:
            return

        # ----- aktuelle Zeile löschen -----

        del self.grid[self.current_line]
        self.grid.insert(0, [0] * GRID_WIDTH)

        # nächste Zeile vorhanden?
        if self.lines_to_clear:

            # nächste Zeile animieren
            self.current_line = self.lines_to_clear.pop(0)
            self.anim_t = 0
            self.animation_timer = 0

            return

        # ----- jetzt sind alle Reihen gelöscht -----

        cleared = 0

        # Anzahl gelöschter Reihen berechnen
        # (1 + die bereits gelöschten)
        cleared = self.lines_cleared_pending

        points = [0, 100, 300, 500, 800]

        self.score += points[cleared] * self.level
        self.lines_cleared += cleared
        self.level = self.lines_cleared // 10 + 1

        # neuer Stein
        self.current_piece = self.next_piece
        self.next_piece = self.new_piece()

        if not self.valid_position(
                self.current_piece["shape"],
                self.current_piece["x"],
                self.current_piece["y"]):
            self.game_over = True

        self.current_line = None
        self.anim_t = 0
        self.state = "PLAY"

    def drop(self):
        if self.valid_position(self.current_piece['shape'],
                               self.current_piece['x'],
                               self.current_piece['y'] + 1):
            self.current_piece['y'] += 1
            return True
        else:
            self.lock_piece()
            return False

    def hard_drop(self):
        while self.drop():
            self.score += 2

    def move(self, dx):
        if self.valid_position(self.current_piece['shape'],
                               self.current_piece['x'] + dx,
                               self.current_piece['y']):
            self.current_piece['x'] += dx

    def rotate_piece(self):
        rotated = self.rotate(self.current_piece['shape'])
        if self.valid_position(rotated, self.current_piece['x'], self.current_piece['y']):
            self.current_piece['shape'] = rotated
        # Wall kick
        elif self.valid_position(rotated, self.current_piece['x'] - 1, self.current_piece['y']):
            self.current_piece['x'] -= 1
            self.current_piece['shape'] = rotated
        elif self.valid_position(rotated, self.current_piece['x'] + 1, self.current_piece['y']):
            self.current_piece['x'] += 1
            self.current_piece['shape'] = rotated

    def draw_block(self, x, y, color_idx, offset_x=SIDE_MARGIN):
        color = COLORS[color_idx]
        rect = pygame.Rect(
            offset_x + x * BLOCK_SIZE,
            y * BLOCK_SIZE,
            BLOCK_SIZE - 1,
            BLOCK_SIZE - 1
        )
        pygame.draw.rect(self.screen, color, rect)
        if color_idx:
            # 3D-Effekt
            pygame.draw.line(self.screen, tuple(min(c + 50, 255) for c in color),
                           rect.topleft, rect.topright)
            pygame.draw.line(self.screen, tuple(min(c + 50, 255) for c in color),
                           rect.topleft, rect.bottomleft)

    def draw_line_animation(self):

        center = (GRID_WIDTH - 1) / 2
        SPREAD = 15

        for x in range(GRID_WIDTH):

            value = self.grid[self.current_line][x]

            if not value:
                continue

            delay = abs(x - center) * DELAY
            local_t = self.anim_t - delay

            if local_t <= 0:
                continue

            elif local_t < GROW:

                scale = 1 + (MAX_SCALE - 1) * (local_t / GROW)
                flash = 1 - (local_t / GROW)

            elif local_t < GROW + SHRINK:

                p = (local_t - GROW) / SHRINK
                scale = MAX_SCALE * (1 - p)
                flash = 0

            else:
                continue

            offset = x - center

            cx = (SIDE_MARGIN + x * BLOCK_SIZE + BLOCK_SIZE / 2 + offset * SPREAD * (scale - 1) / (MAX_SCALE - 1))
            cy = self.current_line * BLOCK_SIZE + BLOCK_SIZE / 2

            size = BLOCK_SIZE * scale

            rect = pygame.Rect(cx - size / 2, cy - size / 2, size - 1, size - 1,)

            color = COLORS[value]

            if flash > 0:
                color = tuple(min(255, int(c + (255 - c) * flash)) for c in color)

            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.line(self.screen, tuple(min(c + 50, 255) for c in color), rect.topleft, rect.topright,)
            pygame.draw.line(self.screen, tuple(min(c + 50, 255) for c in color), rect.topleft, rect.bottomleft,)

    def draw(self):
        self.screen.fill((20, 20, 20))
        
        # Spielfeld-Rahmen
        pygame.draw.rect(self.screen, (50, 50, 50),
                        (SIDE_MARGIN, 0, GRID_WIDTH * BLOCK_SIZE, GRID_HEIGHT * BLOCK_SIZE), 2)
        
        # Grid zeichnen
        for y in range(GRID_HEIGHT):

            if self.state == "ANIMATION" and y == self.current_line:
                continue

            for x in range(GRID_WIDTH):
                self.draw_block(x, y, self.grid[y][x])

        if self.state == "ANIMATION":
            self.draw_line_animation()

        # Aktuelles Stück zeichnen
        shape = self.current_piece['shape']
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    self.draw_block(self.current_piece['x'] + x, self.current_piece['y'] + y, cell)
        
        # Seitenleiste
        left_x = 20
        right_x = sidebar_x = SIDE_MARGIN + GRID_WIDTH * BLOCK_SIZE + 20
        
        # ----- SCORE -----
        label = self.font.render("SCORE", True, (180, 180, 180))
        self.screen.blit(label, (left_x, 25))

        value = self.font_large.render(str(self.score), True, (210, 235, 255))
        self.screen.blit(value, (left_x, 50))


        # ----- LEVEL -----
        label = self.font.render("LEVEL", True, (180, 180, 180))
        self.screen.blit(label, (left_x, 140))

        value = self.font_large.render(str(self.level), True, (170, 205, 240))
        self.screen.blit(value, (left_x, 165))


        # ----- LINES -----
        label = self.font.render("LINES", True, (180, 180, 180))
        self.screen.blit(label, (left_x, 255))

        value = self.font_large.render(str(self.lines_cleared), True, (120, 165, 210))
        self.screen.blit(value, (left_x, 280))

        # Nächstes Stück
        next_text = self.font.render("NEXT", True, (180, 180, 180))
        self.screen.blit(next_text, (right_x, 20))
        
        for y, row in enumerate(self.next_piece['shape']):
            for x, cell in enumerate(row):
                if cell:
                    self.draw_block(GRID_WIDTH + 1 + x, 4 + y, cell)
        
        # Game Over
        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0, 0))
            
            go_text = self.font_large.render("GAME OVER", True, (255, 0, 0))
            rect = go_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
            self.screen.blit(go_text, rect)
            
            restart_text = self.font.render("R = Restart | ESC = Quit", True, (255, 255, 255))
            rect2 = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
            self.screen.blit(restart_text, rect2)
        
        pygame.display.flip()

    def run(self):
        fall_time = 0
        fall_speed = 500  # Millisekunden
        
        running = True
        while running:
            dt = self.clock.tick(60)

            if self.state == "ANIMATION":
                self.update_animation(dt)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif self.game_over:
                        if event.key == pygame.K_r:
                            self.reset_game()
                    else:
                        if event.key == pygame.K_LEFT:
                            self.move(-1)
                        elif event.key == pygame.K_RIGHT:
                            self.move(1)
                        elif event.key == pygame.K_DOWN:
                            self.drop()
                            self.score += 1
                        elif event.key == pygame.K_UP:
                            self.rotate_piece()
                        elif event.key == pygame.K_SPACE:
                            self.hard_drop()
                            line_fall_sound.play()
            
            if self.state == "PLAY" and not self.game_over:
                fall_time += dt
                fall_speed = max(100, 500 - (self.level - 1) * 20)

                if fall_time >= fall_speed:
                    self.drop()
                    fall_time = 0

            self.draw()
        
        pygame.quit()


if __name__ == "__main__":
    game = Tetris()
    game.run()
