#
#   Tetris mit Rollanzeige
#

import pygame
import random
import os
import math

BASE = os.path.dirname(os.path.abspath(__file__))

# Initialisierung von Pygame und dem Sound-System
pygame.init()
pygame.mixer.init()

# --- Soundsicherungen (Verhindert Abstürze bei fehlenden Dateien) ---
try:
    line_clear_sound = pygame.mixer.Sound(os.path.join(BASE, "whoosh.wav"))
    line_clear_sound.set_volume(0.6)
except:
    line_clear_sound = None

try:
    tick = pygame.mixer.Sound(os.path.join(BASE, "gear.wav"))
    tick.set_volume(0.5)
except:
    tick = None

# --- Spielfeld-Konstanten ---
BLOCK_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
GROW = 12
SHRINK = 18
MAX_SCALE = 1.6
DELAY = 2

SIDE_MARGIN = BLOCK_SIZE * 6
SCREEN_WIDTH = BLOCK_SIZE * (GRID_WIDTH + 12)
SCREEN_HEIGHT = BLOCK_SIZE * GRID_HEIGHT

# --- Design-Einstellungen für die Walzen-Anzeigen ---
FONT_NAME = "Arial"
FONT_SIZE = 38  

TEXT_COLOR = (220, 235, 255)
DIGIT_SPACING = 2

ENABLE_WOBBLE = True
ENABLE_ZOOM = True
ENABLE_TICK_SOUND = True

WOBBLE_STRENGTH = 2.0
ZOOM_STRENGTH = 0.06

VISIBLE_PIECES = 7
ROLL_TIME = 1.5

# --- Farben (0 ist Hintergrund) ---
COLORS = [
    (20, 20, 20),     # Dunkelgrau für das Gitter
    (0, 240, 240),    # Cyan (I)
    (240, 240, 0),    # Gelb (O)
    (160, 0, 240),    # Lila (T)
    (0, 240, 0),      # Grün (S)
    (240, 0, 0),      # Rot (Z)
    (0, 0, 240),      # Blau (J)
    (240, 160, 0),    # Orange (L)
]

# --- Die 7 klassischen Tetris-Formen ---
SHAPES = [
    [[1, 1, 1, 1]],
    [[2, 2], [2, 2]],
    [[0, 3, 0], [3, 3, 3]],
    [[0, 4, 4], [4, 4, 0]],
    [[5, 5, 0], [0, 5, 5]],
    [[6, 0, 0], [6, 6, 6]],
    [[0, 0, 7], [7, 7, 7]],
]

class RollDigit:
    def __init__(self, x, y, color=TEXT_COLOR):
        self.x = x
        self.y = y
        self.font = pygame.font.SysFont(FONT_NAME, FONT_SIZE, bold=True)
        self.images = [self.font.render(str(i), True, color) for i in range(10)]
        self.w = self.images[0].get_width()
        self.h = self.images[0].get_height()

        self.pos = 0.0
        self.start = 0.0
        self.target = 0.0
        self.elapsed = 0.0
        self.duration = 0.0
        self.running = False

    def digit(self):
        return int(self.pos) % 10

    def set_digit(self, digit, extra_turns=0):
        current = self.digit()
        steps = (digit - current) % 10
        self.target = self.pos + steps + extra_turns * 10
        self.start = self.pos
        steps_total = self.target - self.start
        self.duration = min(1.2, 0.18 + math.sqrt(steps_total) * 0.09)
        self.elapsed = 0.0
        self.running = True

    def update(self, dt):
        if not self.running:
            return
        self.elapsed += dt
        t = self.elapsed / self.duration
        if t >= 1.0:
            t = 1.0

        # Cosinus-Bremskurve für das Las-Vegas-Gefühl
        ease = 0.5 - 0.5 * math.cos(math.pi * t)
        old_pos = self.pos
        self.pos = self.start + (self.target - self.start) * ease

        prev = int(old_pos)
        curr = int(self.pos)

        while curr > prev:
            prev += 1
            if ENABLE_TICK_SOUND and tick:
                ch = pygame.mixer.find_channel(True)
                if ch:
                    ch.play(tick)

        if t >= 1.0:
            self.pos = float(round(self.target))
            self.running = False

    def draw(self, screen):
        if self.running:
            base = int(math.floor(self.pos))
            frac = self.pos - base
        else:
            base = int(round(self.pos))
            frac = 0.0

        upper = base % 10
        lower = (base + 1) % 10
        offset = frac * self.h

        wobble = 0.0
        scale = 1.0
        if ENABLE_WOBBLE:
            wobble = math.sin(self.pos * 3.0) * WOBBLE_STRENGTH
        if ENABLE_ZOOM:
            scale = 1.0 - (abs(frac - 0.5) * 2) * ZOOM_STRENGTH

        surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        upper_img = self.images[upper]
        lower_img = self.images[lower]

        if scale != 1.0:
            uw, uh = int(self.w * scale), int(self.h * scale)
            upper_img = pygame.transform.smoothscale(upper_img, (uw, uh))
            lower_img = pygame.transform.smoothscale(lower_img, (uw, uh))

        surf.blit(upper_img, (0, -offset))
        surf.blit(lower_img, (0, self.h - offset))
        screen.blit(surf, (self.x + wobble, self.y))


class RollNumber:
    def __init__(self, x, y, digits, color=TEXT_COLOR):
        self.x = x
        self.y = y
        self.digits = digits
        self.value = 0

        tmp_font = pygame.font.SysFont(FONT_NAME, FONT_SIZE, bold=True)
        tmp = tmp_font.render("0", True, color)
        w = tmp.get_width()

        self.items = []
        for i in range(digits):
            self.items.append(RollDigit(x + i * (w + DIGIT_SPACING), y, color))

    def set_value(self, value, extra_turns=0):
        delta = max(0, value - self.value)
        self.value = value
        text = str(value).zfill(self.digits)

        for i, ch in enumerate(text):
            digit = int(ch)
            place = 10 ** (self.digits - i - 1)
            turns = delta // place
            self.items[i].set_digit(digit, turns + extra_turns)

    def update(self, dt):
        if dt > 1.0:
            dt /= 1000.0
        for d in self.items:
            d.update(dt)

    def draw(self, screen):
        for d in self.items:
            d.draw(screen)

    def busy(self):
        return any(d.running for d in self.items)

class SlotWheel:
    def __init__(self, x, y, size):
        self.x = x
        self.y = y
        self.size = size
        self.last_step = -1

        self.running = False
        self.t = 0.0
        self.sequence = []
        self.offset = 0.0
        self.result = 0
        self.tick_sound = None

        try:
            self.tick_sound = pygame.mixer.Sound(os.path.join(BASE, "tick.wav"))
            self.tick_sound.set_volume(0.5)
        except:
            pass

    def build_sequence(self, target):
        length = VISIBLE_PIECES + random.randint(6, 10)
        seq = [random.randint(1, 7) for _ in range(length)]
        seq.append(target)
        self.sequence = seq
        self.offset = 0.0

    def start(self, target):
        self.build_sequence(target)
        self.t = 0.0
        self.running = True

    def ease_out(self, t):
        return 1 - (1 - t) ** 4

    def draw_piece(self, surf, shape, color_id, x, y, scale=1.0):
        color = COLORS[color_id]
        for r, row in enumerate(shape):
            for c, cell in enumerate(row):
                if not cell:
                    continue
                rect = pygame.Rect(x + c * 30 * scale, y + r * 30 * scale, 30 * scale - 2, 30 * scale - 2)
                pygame.draw.rect(surf, color, rect)
                hi = tuple(min(255, v + 60) for v in color)
                pygame.draw.line(surf, hi, rect.topleft, rect.topright, 1)
                pygame.draw.line(surf, hi, rect.topleft, rect.bottomleft, 1)

    def update(self, dt):
        if not self.running:
            return

        self.t += dt / ROLL_TIME

        if self.t >= 1:
            self.t = 1
            self.running = False
            self.result = self.sequence[-1]

        eased = self.ease_out(self.t)
        max_scroll = len(self.sequence) - 1
        self.offset = eased * max_scroll

        step = int(self.offset)
        if step != self.last_step:
            self.last_step = step
            if self.tick_sound:
                ch = pygame.mixer.find_channel(True)
                if ch:
                    ch.play(self.tick_sound)

    def draw(self, screen):
        clip = pygame.Rect(self.x, self.y, self.size, self.size)
        screen.set_clip(clip)

        base_x = self.x + 10
        base_y = self.y + 10
        ITEM_HEIGHT = 120

        for i, val in enumerate(self.sequence):
            shape = SHAPES[val - 1]
            slot_y = base_y + (i - self.offset) * ITEM_HEIGHT
            dist = abs(i - self.offset)

            scale = 1.0 + max(0, 0.08 - dist * 0.02)
            wob = math.sin((i - self.offset) * 2) * 2

            shape_h = len(shape) * 30 * scale
            piece_y = slot_y + (ITEM_HEIGHT - shape_h) / 2

            self.draw_piece(screen, shape, val, base_x + wob, piece_y, scale)

        screen.set_clip(None)
        pygame.draw.rect(screen, (70, 70, 70), (self.x, self.y, self.size, self.size), 2)

class Tetris:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Tetris mit Roll-Anzeigen")
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
        self.wheel = SlotWheel(SIDE_MARGIN + GRID_WIDTH * BLOCK_SIZE + 20, 60, BLOCK_SIZE * 4 + 20)
        
        target_id = SHAPES.index(self.next_piece['shape']) + 1
        self.wheel.start(target_id)

        left_x = 20
        self.score_display = RollNumber(left_x, 50, 6, color=(210, 235, 255))
        self.level_display = RollNumber(left_x, 165, 2, color=(170, 205, 240))
        self.lines_display = RollNumber(left_x, 280, 3, color=(120, 165, 210))
        
        self.score_display.set_value(0)
        self.level_display.set_value(1)
        self.lines_display.set_value(0)

    def new_piece(self):
        shape = random.choice(SHAPES)
        return {
            'shape': [row[:] for row in shape],
            'x': GRID_WIDTH // 2 - len(shape[0]) // 2,
            'y': 0
        }

    def check_game_over(self):
        return not self.valid_position(
            self.current_piece["shape"],
            self.current_piece["x"],
            self.current_piece["y"]
        )

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

        self.lines_cleared_pending = len(self.lines_to_clear)

        if self.lines_to_clear:
            self.current_line = self.lines_to_clear.pop(0)
            self.anim_t = 0
            self.animation_timer = 0
            self.state = "ANIMATION"

            if line_clear_sound:
                ch = pygame.mixer.find_channel(True)
                if ch:
                    ch.play(line_clear_sound)
            return
        else:
            self.current_piece = self.next_piece
            self.next_piece = self.new_piece()

            target_id = SHAPES.index(self.next_piece['shape']) + 1
            self.wheel.start(target_id)
            self.wheel.t = 0            

            self.current_piece["x"] = GRID_WIDTH // 2 - len(self.current_piece["shape"][0]) // 2
            self.current_piece["y"] = 0

            if not self.valid_position(
                    self.current_piece["shape"],
                    self.current_piece["x"],
                    self.current_piece["y"]):
                self.game_over = True
                return

            self.state = "PLAY"

    def update_animation(self, dt):
        self.animation_timer += dt
        self.anim_t += 1

        if self.animation_timer < 500:
            return

        if self.state != "ANIMATION":
            return

        points_per_line = 100 * self.level
        self.score += points_per_line
        
        self.lines_cleared += 1
        self.level = self.lines_cleared // 10 + 1

        self.score_display.set_value(self.score, extra_turns=1)
        self.lines_display.set_value(self.lines_cleared, extra_turns=0)

        del self.grid[self.current_line]
        self.grid.insert(0, [0] * GRID_WIDTH)

        if self.lines_to_clear:
            self.lines_to_clear = [y + 1 if y < self.current_line else y for y in self.lines_to_clear]
            self.current_line = self.lines_to_clear.pop(0)
            self.anim_t = 0
            self.animation_timer = 0
            
            if line_clear_sound:
                ch = pygame.mixer.find_channel(True)
                if ch:
                    ch.play(line_clear_sound)
            return

        if self.lines_cleared_pending >= 3:
            self.score += 200 * self.lines_cleared_pending * self.level
            self.score_display.set_value(self.score, extra_turns=3)
            if self.level_display.value != self.level:
                self.level_display.set_value(self.level, extra_turns=1)

        self.current_line = None
        self.anim_t = 0

        self.current_piece = self.next_piece
        self.next_piece = self.new_piece()

        target_id = SHAPES.index(self.next_piece['shape']) + 1
        self.wheel.start(target_id)
        self.wheel.t = 0

        self.state = "PLAY"
        self.current_piece["x"] = GRID_WIDTH // 2 - len(self.current_piece["shape"]) // 2
        self.current_piece["y"] = 0
        self.game_over = False

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
        self.score_display.set_value(self.score, extra_turns=0)

    def move(self, dx):
        if self.valid_position(self.current_piece['shape'],
                               self.current_piece['x'] + dx,
                               self.current_piece['y']):
            self.current_piece['x'] += dx

    def rotate_piece(self):
        rotated = self.rotate(self.current_piece['shape'])
        if self.valid_position(rotated, self.current_piece['x'], self.current_piece['y']):
            self.current_piece['shape'] = rotated
        elif self.valid_position(rotated, self.current_piece['x'] - 1, self.current_piece['y']):
            self.current_piece['x'] -= 1
            self.current_piece['shape'] = rotated
        elif self.valid_position(rotated, self.current_piece['x'] + 1, self.current_piece['y']):
            self.current_piece['x'] += 1
            self.current_piece['shape'] = rotated

    def draw_block(self, x, y, color_idx, offset_x=SIDE_MARGIN):
        color = COLORS[color_idx]
        rect = pygame.Rect(offset_x + x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE - 1, BLOCK_SIZE - 1)
        pygame.draw.rect(self.screen, color, rect)
        if color_idx:
            pygame.draw.line(self.screen, tuple(min(c + 50, 255) for c in color), rect.topleft, rect.topright)
            pygame.draw.line(self.screen, tuple(min(c + 50, 255) for c in color), rect.topleft, rect.bottomleft)

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
            rect = pygame.Rect(cx - size / 2, cy - size / 2, size - 1, size - 1)
            color = COLORS[value]

            if flash > 0:
                color = tuple(min(255, int(c + (255 - c) * flash)) for c in color)

            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.line(self.screen, tuple(min(c + 50, 255) for c in color), rect.topleft, rect.topright)
            pygame.draw.line(self.screen, tuple(min(c + 50, 255) for c in color), rect.topleft, rect.bottomleft)

    def draw(self):
        self.screen.fill((20, 20, 20))
        pygame.draw.rect(self.screen, (50, 50, 50), (SIDE_MARGIN, 0, GRID_WIDTH * BLOCK_SIZE, GRID_HEIGHT * BLOCK_SIZE), 2)
        
        for y in range(GRID_HEIGHT):
            if self.state == "ANIMATION" and y == self.current_line:
                continue
            for x in range(GRID_WIDTH):
                self.draw_block(x, y, self.grid[y][x])

        if self.state == "ANIMATION":
            self.draw_line_animation()

        if self.state != "ANIMATION" and not self.game_over:
            shape = self.current_piece['shape']
            for y, row in enumerate(shape):
                for x, cell in enumerate(row):
                    if cell:
                        self.draw_block(self.current_piece['x'] + x, self.current_piece['y'] + y, cell)

        left_x = 20
        right_x = SIDE_MARGIN + GRID_WIDTH * BLOCK_SIZE + 20
        
        label = self.font.render("SCORE", True, (180, 180, 180))
        self.screen.blit(label, (left_x, 25))
        label = self.font.render("LEVEL", True, (180, 180, 180))
        self.screen.blit(label, (left_x, 140))
        label = self.font.render("LINES", True, (180, 180, 180))
        self.screen.blit(label, (left_x, 255))

        self.score_display.draw(self.screen)
        self.level_display.draw(self.screen)
        self.lines_display.draw(self.screen)

        next_text = self.font.render("NEXT", True, (180, 180, 180))
        self.screen.blit(next_text, (right_x, 20))
        self.wheel.draw(self.screen)

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
        running = True
        while running:
            dt = self.clock.tick(60)

            if self.state == "ANIMATION":
                self.update_animation(dt)

            self.score_display.update(dt)
            self.level_display.update(dt)
            self.lines_display.update(dt)
            dt_s = dt / 1000.0
            self.wheel.update(dt_s)

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
                            self.score_display.set_value(self.score, extra_turns=0)
                        elif event.key == pygame.K_UP:
                            self.rotate_piece()
                        elif event.key == pygame.K_SPACE:
                            self.hard_drop()
            
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
