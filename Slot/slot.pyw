# ============================================================
# Slot Machine - Score Machine
# ============================================================

import pygame
import random
import os
import math

BASE = os.path.dirname(os.path.abspath(__file__))

pygame.init()
pygame.mixer.init()

# --- Sound-Management (Crash-Sicherung) ---
try:
    tick_sound = pygame.mixer.Sound(os.path.join(BASE, "tick.wav"))
    tick_sound.set_volume(0.3)
except:
    tick_sound = None

try:
    stop_sound = pygame.mixer.Sound(os.path.join(BASE, "tick1.wav"))
    stop_sound.set_volume(0.3)
except:
    stop_sound = None

try:
    jackpot_sound = pygame.mixer.Sound(os.path.join(BASE, "muenze2.wav"))
    jackpot_sound.set_volume(0.8)
except:
    jackpot_sound = None

try:
    coin_sound1 = pygame.mixer.Sound(os.path.join(BASE, "coin_sound.wav"))
    coin_sound1.set_volume(0.1)
except:
    coin_sound1 = None

# --- Konstanten & Design-Einstellungen ---
BLOCK_SIZE = 26
ITEM_GAP = 18
ITEM_HEIGHT = BLOCK_SIZE * 4 + ITEM_GAP
SCREEN_WIDTH = 560
SCREEN_HEIGHT = 600
FPS = 60
VISIBLE_PIECES = 7
ROLL_TIME = 1.5
WOBBLE = True
ZOOM = True

BG = (18, 18, 22)
FRAME = (170, 170, 170)
TEXT = (220, 235, 255)
WINDOW_BG = (35, 35, 40)
WIN_RED = (255, 55, 55)
WINDOW_SIZE = BLOCK_SIZE * 4 + 20

FLASH_SPEED = 20        
JACKPOT_SPEED = 18      

# Spielzustände (States)
IDLE = 0
SPINNING = 1
FLASH = 2
JACKPOT = 3
PAYING = 4

COLORS = [
    (0, 0, 0),
    (0, 240, 240),    # Cyan
    (240, 240, 0),    # Gelb
    (160, 0, 240),    # Lila
    (0, 240, 0),      # Grün
    (240, 0, 0),      # Rot
    (0, 0, 240),      # Blau
    (240, 160, 0),    # Orange
]

SHAPES = [
    [[1, 1, 1, 1]],
    [[2, 2], [2, 2]],
    [[0, 3, 0], [3, 3, 3]],
    [[0, 4, 4], [4, 4, 0]],
    [[5, 5, 0], [0, 5, 5]],
    [[6, 0, 0], [6, 6, 6]],
    [[0, 0, 7], [7, 7, 7]],
]


class SlotWheel:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.running = False
        self.t = 0.0
        self.stop_played = False

        self.sequence = [random.randint(1, 7) for _ in range(VISIBLE_PIECES)]
        self.offset = VISIBLE_PIECES // 2
        self.result = self.sequence[VISIBLE_PIECES // 2]

        self.roll_time = ROLL_TIME
        self.delay = 0.0
        self.elapsed = 0.0
        self.bounce = 0

    def build_sequence(self, target):
        seq = self.sequence.copy()
        length = random.randint(6, 10)

        for _ in range(length):
            seq.append(random.randint(1, 7))

        seq.append(target)
        self.sequence = seq
        self.offset = VISIBLE_PIECES // 2

    def start(self, target, delay=0.0):
        self.build_sequence(target)
        self.t = 0.0
        self.delay = delay
        self.elapsed = 0.0
        self.stop_played = False

        if delay <= 0:
            self.running = True
        else:
            self.running = False

    def ease_out(self, t):
        return 1 - pow(1 - t, 4)

    def draw_piece(self, surf, shape, color_id, x, y, scale=1.0):
        color = COLORS[color_id]
        for r, row in enumerate(shape):
            for c, cell in enumerate(row):
                if not cell:
                    continue
                rect = pygame.Rect(x + c * BLOCK_SIZE * scale,
                                   y + r * BLOCK_SIZE * scale,
                                   BLOCK_SIZE * scale - 2,
                                   BLOCK_SIZE * scale - 2)

                pygame.draw.rect(surf, color, rect)
                hi = tuple(min(255, v + 60) for v in color)
                pygame.draw.line(surf, hi, rect.topleft, rect.topright, 1)
                pygame.draw.line(surf, hi, rect.topleft, rect.bottomleft, 1)

    def update(self, dt):
        if not self.running:
            if self.delay > 0:
                self.elapsed += dt
                if self.elapsed >= self.delay:
                    self.running = True
                    self.delay = 0.0
                else:
                    return
            else:
                return

        self.t += dt / self.roll_time

        if self.t >= 1:
            self.t = 1
            self.running = False
            self.result = self.sequence[-1]

            if stop_sound and not self.stop_played:
                channel = pygame.mixer.find_channel(True)
                if channel:
                    channel.play(stop_sound)
                self.stop_played = True

        eased = self.ease_out(self.t)
        max_scroll = len(self.sequence) - 1
        new_offset = eased * max_scroll

        if int(new_offset * 10) != int(self.offset * 10):
            if tick_sound:
                channel = pygame.mixer.find_channel(True)
                if channel:
                    channel.play(tick_sound)
                    
        self.offset = new_offset

        if self.t > 0.92:
            p = (self.t - 0.92) / 0.08  
            self.bounce = math.sin(p * math.pi * 2.5) * (1 - p) * 8

    def draw(self, screen):
        clip = pygame.Rect(self.x, self.y, WINDOW_SIZE, WINDOW_SIZE)
        screen.set_clip(clip)

        base_x = self.x + 10
        base_y = self.y + 10

        for i, val in enumerate(self.sequence):
            shape = SHAPES[val - 1]
            slot_y = (base_y + (i - self.offset) * ITEM_HEIGHT + self.bounce)
            dist = abs(i - self.offset)
            
            scale = 1.0
            if ZOOM:
                scale += (math.sin((i - self.offset) * 0.6) * 0.03)

            scale += max(0, 0.08 - dist * 0.02)
            wob = 0
            if WOBBLE:
                wob = (math.sin((i - self.offset) * 2) * 2)

            shape_h = (len(shape) * BLOCK_SIZE * scale)
            piece_y = (slot_y + (ITEM_HEIGHT - shape_h) / 2)

            self.draw_piece(screen, shape, val, base_x + wob, piece_y, scale)

        screen.set_clip(None)

        fade = pygame.Surface((WINDOW_SIZE, 22), pygame.SRCALPHA)
        for y in range(22):
            alpha = int(180 * (1 - y / 22))
            pygame.draw.line(fade, (0, 0, 0, alpha), (0, y), (WINDOW_SIZE, y))
            
        screen.blit(fade, (self.x, self.y))
        screen.blit(pygame.transform.flip(fade, False, True), (self.x, self.y + WINDOW_SIZE - 22))

# ============================================================
# SlotMachine Hauptklasse (Spiellogik, Cheats & Gewinnstufen)
# ============================================================
class SlotMachine:
    def __init__(self):
        self.state = IDLE

        # Geldsystem & Auszahlungssteuerung
        self.credit = 100
        self.bet = 1
        self.win = 0
        self.win_cooldown = 0  # Sperrt Gewinne nach Glückssträhnen
        self.cheat_spin = False

        # Münzauszahlung per Zeitsteuerung
        self.pay_speed = 10  
        self.pay_timer = 0.0

        self.window_colors = [WINDOW_BG] * 3
        self.anim_time = 0.0
        self.anim_duration = 0.0
        self.flash_windows = []
        
        gap = 25
        total_width = (WINDOW_SIZE * 3 + gap * 2)
        start_x = (SCREEN_WIDTH - total_width) // 2
        y = 280

        # Die 3 Walzen vorbereiten
        self.wheels = [
            SlotWheel(start_x, y),
            SlotWheel(start_x + WINDOW_SIZE + gap, y),
            SlotWheel(start_x + (WINDOW_SIZE + gap) * 2, y)
        ]

        # Unterschiedliche Geschwindigkeiten für den Casino-Effekt
        self.wheels[0].roll_time = 1.0
        self.wheels[1].roll_time = 1.2
        self.wheels[2].roll_time = 1.8

        self.message_time = 0.0

    def lerp_color(self, c1, c2, t):  # Lineare Farbmischung für Blinkeffekte
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
        )

    def is_win(self, a, b, c):
        return a == b or a == c or b == c

    def calc_win(self):
        a = self.wheels[0].result
        b = self.wheels[1].result
        c = self.wheels[2].result

        if a == b == c:
            return self.bet * 20
        if self.is_win(a, b, c):
            return self.bet * 4
        return 0

    def check_win(self):
        self.win = self.calc_win()

        a = self.wheels[0].result
        b = self.wheels[1].result
        c = self.wheels[2].result

        if not self.cheat_spin:
            if a == b == c:
                self.win_cooldown = 5
            elif self.is_win(a, b, c):
                self.win_cooldown = 3

        if a == b == c:
            self.flash_windows = [0, 1, 2]
            self.state = JACKPOT
            self.message_time = 0.0
            if jackpot_sound:
                jackpot_sound.play()
        elif a == b:
            self.flash_windows = [0, 1]
            self.state = FLASH
            self.message_time = 0.0
        elif a == c:
            self.flash_windows = [0, 2]
            self.state = FLASH
            self.message_time = 0.0
        elif b == c:
            self.flash_windows = [1, 2]
            self.state = FLASH
            self.message_time = 0.0
        else:
            self.state = IDLE
        self.anim_time = 0.0

    def spin(self, cheat=None):
        if self.state != IDLE:
            return
        if self.credit < self.bet:
            return

        self.credit -= self.bet
        self.win = 0
        self.cheat_spin = cheat is not None
        self.state = SPINNING
        self.window_colors = [WINDOW_BG] * 3

        if cheat == "THREE":  # Cheat "d"
            a = random.randint(1, 7)
            b = a
            c = a
        elif cheat == "TWO":  # Cheat "z"
            a = random.randint(1, 7)
            b = a
            while True:
                c = random.randint(1, 7)
                if c != a:
                    break

            mode = random.randint(0, 2)
            if mode == 0:
                targets = [a, b, c]
            elif mode == 1:
                targets = [a, c, a]
            else:
                targets = [c, a, a]
            a, b, c = targets
        else:
            if self.win_cooldown > 0:
                while True:
                    a = random.randint(1, 7)
                    b = random.randint(1, 7)
                    c = random.randint(1, 7)
                    if not self.is_win(a, b, c):
                        break
                self.win_cooldown -= 1
            else:
                a = random.randint(1, 7)
                b = random.randint(1, 7)
                c = random.randint(1, 7)

        self.wheels[0].start(a, 0.0)
        self.wheels[1].start(b, 0.35)
        self.wheels[2].start(c, 0.7)

    def update(self, dt):
        if self.state == FLASH or self.state == JACKPOT:
            self.message_time += dt
        else:
            self.message_time = 0.0

        for wheel in self.wheels:
            wheel.update(dt)

        if self.state == SPINNING:
            if all(not w.running for w in self.wheels):
                self.check_win()

        elif self.state == FLASH:
            self.anim_time += dt
            pulse = (math.sin(self.anim_time * FLASH_SPEED) + 1) / 2
            color = self.lerp_color(WINDOW_BG, WIN_RED, pulse)
            self.window_colors = [WINDOW_BG] * 3

            for i in self.flash_windows:
                self.window_colors[i] = color

            if self.anim_time > 1.2:
                self.window_colors = [WINDOW_BG] * 3
                self.pay_timer = 0.0
                self.state = PAYING

        elif self.state == JACKPOT:
            self.anim_time += dt
            phase = self.anim_time * JACKPOT_SPEED
            self.window_colors = [WINDOW_BG] * 3

            for i in range(3):
                pulse = (math.sin(phase - i * 2.1) + 1) / 2
                self.window_colors[i] = self.lerp_color(WINDOW_BG, WIN_RED, pulse)

            if self.anim_time > 2.5:
                self.window_colors = [WINDOW_BG] * 3
                self.pay_timer = 0.0
                self.state = PAYING

        elif self.state == PAYING:
            self.pay_timer += dt
            while self.pay_timer >= 1 / self.pay_speed and self.win > 0:
                self.pay_timer -= 1 / self.pay_speed
                self.credit += 1
                self.win -= 1

                if coin_sound1:
                    channel = pygame.mixer.find_channel(True)
                    if channel:
                        channel.play(coin_sound1)

            if self.win <= 0:
                self.state = IDLE

    def draw(self, screen):
        for i, wheel in enumerate(self.wheels):
            rect = pygame.Rect(wheel.x, wheel.y, WINDOW_SIZE, WINDOW_SIZE)
            draw_reel_background(screen, rect, self.window_colors[i])
            wheel.draw(screen)
            pygame.draw.rect(screen, FRAME, (wheel.x, wheel.y, WINDOW_SIZE, WINDOW_SIZE), 2)

    def draw_message(self, screen, small_font, big_font):
        if self.state == FLASH:
            t = self.message_time
            if t < 1.8:
                brightness = math.sin(min(t / 1.8, 1.0) * math.pi)
                alpha = int(60 + brightness * 195)
            else:
                alpha = 80
            text = small_font.render("YOU WIN!", True, (255, 255, 255))
            text.set_alpha(alpha)
            x = (SCREEN_WIDTH - text.get_width()) // 2
            y = 445
            screen.blit(text, (x, y))

        elif self.state == JACKPOT:
            pulse_time = self.message_time
            if pulse_time < 2.0:
                pulse = 1.0 + 0.10 * math.sin(pulse_time * math.pi)
                alpha = int(70 + 100 * abs(math.sin(self.message_time * math.pi)))
            else:
                pulse = 1.0
                alpha = 90

            img = big_font.render("JACKPOT", True, (255, 40, 40))
            img.set_alpha(alpha)

            max_width = SCREEN_WIDTH - 40
            if img.get_width() > max_width:
                faktor = max_width / img.get_width()
                img = pygame.transform.smoothscale(img, (int(img.get_width() * faktor), int(img.get_height() * faktor)))

            img = pygame.transform.smoothscale(img, (int(img.get_width() * pulse), int(img.get_height() * 3.0 * pulse)))
            x = (SCREEN_WIDTH - img.get_width()) // 2
            y = 280 + WINDOW_SIZE // 2 - img.get_height() // 2
            screen.blit(img, (x, y))


def draw_display(screen, label_font, display_font, title, value, x, y, width):
    title_img = label_font.render(title, True, (170, 170, 170))
    title_x = x + (width - title_img.get_width()) // 2
    screen.blit(title_img, (title_x, y))
    y += 18

    rect = pygame.Rect(x, y, width, 50)
    pygame.draw.rect(screen, (55, 0, 0), rect)
    pygame.draw.rect(screen, (120, 60, 60), rect, 2)

    pygame.draw.polygon(screen, (120, 80, 80), [
        (x + 3, y + 3),
        (x + width // 2, y + 3),
        (x + width // 2 - 15, y + 12),
        (x + 3, y + 12)
    ])

    brightness = random.randint(235, 255)
    color = (brightness, 35, 35)
    text = f"{value:03d}"

    glow = display_font.render(text, True, color)
    glow.set_alpha(35)
    tx = x + (width - glow.get_width()) // 2
    ty = y + 6

    # 5x5 Glow-Matrix für den Röhren-Effekt
    for dx in (-2, -1, 0, 1, 2):
        for dy in (-2, -1, 0, 1, 2):
            screen.blit(glow, (tx + dx, ty + dy))

    img = display_font.render(text, True, (255, 70, 70))
    screen.blit(img, (tx, ty))


def draw_reel_background(screen, rect, base_color):
    r, g, b = base_color
    for y in range(rect.height):
        d = abs((y / rect.height) - 0.5) * 2
        brightness = 1.60 - d * 0.60  
        color = (min(255, int(r * brightness)), min(255, int(g * brightness)), min(255, int(b * brightness)))
        pygame.draw.line(screen, color, (rect.x, rect.y + y), (rect.x + rect.width, rect.y + y))


def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Slot Machine")
    clock = pygame.time.Clock()
    machine = SlotMachine()

    label_font = pygame.font.SysFont("Arial", 15, bold=True)
    display_font = pygame.font.SysFont("Consolas", 34, bold=True)
    small_font = pygame.font.SysFont("Arial", 30, bold=True)
    big_font = pygame.font.SysFont("Arial Black", 150, bold=True)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    running = False
                if e.key == pygame.K_SPACE:
                    machine.spin()
                if e.key == pygame.K_z:
                    machine.spin("TWO")
                if e.key == pygame.K_d:
                    machine.spin("THREE")

        machine.update(dt)
        screen.fill(BG)

        draw_display(screen, label_font, display_font, "WIN", machine.win, 15, 60, 150)
        draw_display(screen, label_font, display_font, "BET", machine.bet, 205, 60, 150)
        draw_display(screen, label_font, display_font, "CREDIT", machine.credit, 395, 60, 150)

        machine.draw(screen)
        machine.draw_message(screen, small_font, big_font)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()



