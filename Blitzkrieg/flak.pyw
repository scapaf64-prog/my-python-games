# BLITZ - Heavy Flak Edition
# Python + Pygame

import pygame
import math
import random
import array

pygame.init()
pygame.mixer.init()

# Sound
try:
    explosion_sound = pygame.mixer.Sound("whoosh.mp3")
    explosion_sound.set_volume(0.1)
except:
    explosion_sound = None

try:
    shot_sound = pygame.mixer.Sound("mg-fire.mp3")
    shot_sound.set_volume(0.1)
except:
    shot_sound = None

WIDTH, HEIGHT = 1280, 720

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("BLITZ - Heavy Flak")

clock = pygame.time.Clock()

# Farben

SKY1 = (120,190,255)
SKY2 = (180,220,255)

SEA = (30,70,135)

DARK = (30,30,30)
GRAY = (100,100,100)
LIGHT = (170,170,170)

WHITE = (255,255,255)

YELLOW = (255,220,80)
ORANGE = (255,130,40)
RED = (255,50,50)

SMOKE = (120,120,120)

# Klassen

class Plane:

    def __init__(self, zeppelin=False):

        self.hp = 3 if zeppelin else 1

        self.zeppelin = zeppelin

        self.x = random.choice([-200, WIDTH + 200])

        self.y = random.randint(100, 280)

        if self.x < 0:
            self.speed = random.uniform(1.2, 2.0)
        else:
            self.speed = -random.uniform(1.2, 2.0)

    def update(self):

        self.x += self.speed

    def draw(self):

        direction = 1 if self.speed > 0 else -1

        if self.zeppelin:

            color = {3: DARK, 2: GRAY,}.get(self.hp, RED)

            # Zeppelinkörper
            pygame.draw.ellipse(screen, color, (self.x - 90, self.y - 30, 180, 60))

            # Gondel
            pygame.draw.rect(screen, DARK, (self.x - 20, self.y + 14, 40, 18))

            # Bugmarkierung
            pygame.draw.circle(screen, GRAY, (int(self.x + 75 * direction), int(self.y)), 5)

        else:
            x = self.x
            y = self.y

            pts = [
                # Nase
                (x + 40 * direction, y),
                (x + 20 * direction, y - 6),
                (x - 10 * direction, y - 6),

                # obere Tragfläche
                (x - 25 * direction, y - 22),
                (x - 40 * direction, y - 22),
                (x - 18 * direction, y - 6),

                # Heck
                (x - 60 * direction, y - 6),

                # Seitenleitwerk
                (x - 68 * direction, y - 16),
                (x - 75 * direction, y - 16),
                (x - 75 * direction, y + 16),
                (x - 68 * direction, y + 16),
                (x - 60 * direction, y + 6),
                (x - 18 * direction, y + 6),

                # untere Tragfläche
                (x - 40 * direction, y + 22),
                (x - 25 * direction, y + 22),
                (x - 10 * direction, y + 6),
                (x + 20 * direction, y + 6),
            ]

            pygame.draw.polygon(screen, DARK, pts)

            # Motoren
            pygame.draw.circle(screen, GRAY, (int(x - 18 * direction), int(y - 18)), 4)
            pygame.draw.circle(screen, GRAY, (int(x - 18 * direction), int(y + 18)), 4)

class Shell:

    def __init__(self, x, y, dx, dy):

        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.life = 12

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.life -= 1

    def draw(self):

        # heller Schweif

        pygame.draw.line(screen, ORANGE, (self.x - self.dx * 2, self.y - self.dy * 2), (self.x, self.y), 2)
        pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), 4)

class Explosion:

    def __init__(self, x, y):

        self.x = x
        self.y = y

        self.radius = 6
        self.ring = 2
        self.life = 30

    def update(self):

        self.radius += 4.5
        self.ring += 7.5
        self.life -= 1

    def draw(self):

        # INNERER BLITZ
        pygame.draw.circle(screen, ORANGE, (int(self.x), int(self.y)), int(self.radius))

        pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), int(self.radius * 0.55))

        # DRUCKWELLE (Hauptimpuls)
        pygame.draw.circle(screen, (235, 235, 235), (int(self.x), int(self.y)), int(self.ring), 3)

        # zweite Stoßwelle (verzögert / „nachhallend“)
        pygame.draw.circle(screen, (160, 160, 160), (int(self.x), int(self.y)), int(self.ring * 1.25), 2)

        # kleine Staubwolke außen
        pygame.draw.circle(screen, (90, 90, 90), (int(self.x), int(self.y)), int(self.ring * 1.6), 1)

class Smoke:

    def __init__(self, x, y):

        self.x = x
        self.y = y
        self.size = 10
        self.life = 24

    def update(self):

        self.y -= 0.6
        self.size += 1.4
        self.life -= 1

    def draw(self):

        pygame.draw.circle(screen, SMOKE, (int(self.x), int(self.y)), int(self.size))

# Spielvariablen

planes = []
shells = []
explosions = []
smokes = []
muzzle_positions = []

spawn_timer = 0

score = 0
level = 1

fire_delay = 0

# Turm
turret_yaw = 0
turret_pitch = 18

target_yaw = 0
target_pitch = 18

left_recoil = 0
right_recoil = 0

next_barrel = 0   # 0 = links, 1 = rechts
flash_timer = 0
flash_barrel = 0

font = pygame.font.SysFont("consolas", 24)

# Hauptloop

running = True

while running:

    dt = clock.tick(60)

    # EVENTS

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                running = False

    # STEUERUNG

    keys = pygame.key.get_pressed()

    # GEGNER SPAWN 

    spawn_timer -= 1

    if spawn_timer <= 0 and len(planes) < 5:

        zepp = False

        if level >= 3 and random.random() < 0.25:
            zepp = True

        planes.append(Plane(zepp))

        # NUR HIER zurücksetzen
        spawn_timer = random.randint(40, 250)

    if keys[pygame.K_LEFT]:
        target_yaw -= 1.8

    if keys[pygame.K_RIGHT]:
        target_yaw += 1.8

    if keys[pygame.K_UP]:
        target_pitch += 1.0

    if keys[pygame.K_DOWN]:
        target_pitch -= 1.0

    target_pitch = max(-2, min(45, target_pitch))

    # weiches Nachziehen
    turret_yaw += (target_yaw - turret_yaw) * 0.12
    turret_pitch += (target_pitch - turret_pitch) * 0.12

    # FEUERN

    fire_delay -= 1

    if keys[pygame.K_SPACE]:

        if fire_delay <= 0 and len(muzzle_positions) == 2:

            shot_sound.play()

            mx, my, tx, ty = muzzle_positions[next_barrel]
            dx = tx - mx
            dy = ty - my
            dist = math.hypot(dx, dy)

            if dist != 0:
                dx /= dist
                dy /= dist

            speed = 26

            shells.append(
                Shell(mx, my, dx * speed, dy * speed))

            for i in range(6):
                smokes.append(Smoke(mx + random.randint(-12,12), my + random.randint(-12,12)))

            if next_barrel == 0:
                left_recoil = 80
            else:
                right_recoil = 80

            flash_timer = 3
            flash_barrel = next_barrel
            next_barrel = 1 - next_barrel

            fire_delay = 6

    # GEGNER

    for p in planes[:]:

        p.update()

        if p.x < -300 or p.x > WIDTH + 300:
            p.hp -= 1

            if p.hp <= 0:
               planes.remove(p)

    # GRANATEN

    for s in shells[:]:

        s.update()

        for p in planes[:]:

            dist = math.hypot(s.x - p.x, s.y - p.y)

            radius = 52 if p.zeppelin else 30

            if dist < radius:

                # Explosion IMMER beim Treffer
                explosions.append(Explosion(s.x, s.y))

                if explosion_sound:
                    explosion_sound.play()

                score += 200 if p.zeppelin else 100

                p.hp -= 1

                if p.hp <= 0:
                    planes.remove(p)

                if s in shells:
                    shells.remove(s)

                break

        if (s.life <= 0 or s.x < -100 or s.x > WIDTH+100 or s.y < -100):

            if s in shells:
                shells.remove(s)

    # EXPLOSIONEN

    for e in explosions[:]:

        e.update()

        if e.life <= 0:
            explosions.remove(e)

    # SCHMUACH

    for s in smokes[:]:

        s.update()

        if s.life <= 0:
            smokes.remove(s)

    # LEVEL

    level = 1 + score // 1200

    # HINTERGRUND

    screen.fill(SKY1)

    pygame.draw.rect(screen, SEA, (0, HEIGHT//2, WIDTH, HEIGHT//2))

    # FLUGZEUGE

    for p in planes:
        p.draw()

    # GRANATEN

    for s in shells:
        s.draw()

    # EXPLOSIONEN

    for e in explosions:
        e.draw()

    # SCHMUACH

    for s in smokes:
        s.draw()

    # RADAR

    radar_x = WIDTH // 2
    radar_y = HEIGHT - 90

    pygame.draw.circle(screen, DARK, (radar_x, radar_y), 85, 2)

    for p in planes:

        rx = radar_x + int((p.x - WIDTH/2) / 10)
        ry = radar_y - int((p.y - 180) / 6)

        pygame.draw.circle(screen, RED, (rx, ry), 4)

    # CINEMATISCHE DOPPEL-FLAK

    angle_pitch = math.radians(turret_pitch)

    # deutlich stärker nach oben schwenkbar
    elev = math.sin(angle_pitch) * 560

    # kräftiger Rückstoß

    left_recoil *= 0.82
    right_recoil *= 0.82

    if left_recoil < 0.5:
        left_recoil = 0

    if right_recoil < 0.5:
        right_recoil = 0

    # gigantische Rohrbasen

    left_base  = (-40, HEIGHT + 180)
    right_base = (WIDTH + 40, HEIGHT + 180)

    # Zielraum
    center_x = WIDTH // 2
    center_y = HEIGHT - elev - 180

    # Spitzen weiter auseinander

    yaw_offset = turret_yaw * 8
    left_target_x  = center_x - 90 + yaw_offset
    right_target_x = center_x + 90 + yaw_offset

    left_target_y  = center_y
    right_target_y = center_y

    barrel_info = [
        (
            left_base[0],
            left_base[1],
            left_target_x,
            left_target_y
        ),
        (
            right_base[0],
            right_base[1],
            right_target_x,
            right_target_y
        )
    ]

    muzzle_positions = []

    for idx, (bx, by, tx, ty) in enumerate(barrel_info):

        recoil_amount = left_recoil if idx == 0 else right_recoil

        dx = tx - bx
        dy = ty - by

        dist = math.hypot(dx, dy)

        if dist != 0:
            nx = dx / dist
            ny = dy / dist
        else:
            nx = ny = 0

        ex = bx + dx * 0.80 - nx * recoil_amount
        ey = by + dy * 0.80 - ny * recoil_amount

        muzzle_positions.append((ex, ey, tx, ty))

        # EXTREM dick unten
        base_width = 130

        # schmal oben
        muzzle_width = 16

        # Hauptrohr
        pygame.draw.polygon(screen, GRAY, [
            (bx - base_width, by),
            (bx + base_width, by),
            (ex + muzzle_width, ey),
            (ex - muzzle_width, ey)
        ])

        # Metall-Highlight
        pygame.draw.line(screen, LIGHT, (bx - 36, by - 20), (ex - 4, ey - 5), 8)

        # Schatten
        pygame.draw.line(screen, DARK, (bx + 28, by + 8), (ex + 5, ey + 4), 10)

        # Rohr 
        pygame.draw.line(screen, GRAY, (bx, by), (ex, ey), 32)

        # Rohrkappe
        pygame.draw.circle(screen, GRAY, (int(ex), int(ey)), muzzle_width)

    # MÜNDUNGSFEUER

    if keys[pygame.K_SPACE]:

        if flash_timer > 0 and len(muzzle_positions) == 2:

            mx, my, tx, ty = muzzle_positions[flash_barrel]

            # Richtung des Rohres
            dx = tx - mx
            dy = ty - my
            dist = math.hypot(dx, dy)

            if dist != 0:
                dx /= dist
                dy /= dist

            # Senkrechte Richtung
            px = -dy
            py = dx

            start = 60

            fx = mx + dx * start
            fy = my + dy * start

            length = random.randint(70, 110)
            width = random.randint(18, 28)

            tip = (fx + dx * length, fy + dy * length)
            left = (fx + px * width, fy + py * width)
            right = (fx - px * width, fy - py * width)

            # äußere Flamme
            pygame.draw.polygon(screen, ORANGE, [left, tip, right])

            # innere, heiße Flamme
            tip2 = (fx + dx * (length * 0.65), fy + dy * (length * 0.65))
            left2 = ( fx + px * (width * 0.45), fy + py * (width * 0.45))
            right2 = (fx - px * (width * 0.45), fy - py * (width * 0.45))

            pygame.draw.polygon(screen, YELLOW, [left2, tip2, right2])

            # Weißer heißer Kern
            tip3 = (fx + dx * (length * 0.35), fy + dy * (length * 0.35))
            left3 = (fx + px * (width * 0.18), fy + py * (width * 0.18))
            right3 = (fx - px * (width * 0.18), fy - py * (width * 0.18))

            pygame.draw.polygon(screen, WHITE, [left3, tip3, right3])
            pygame.draw.circle(screen, ORANGE, (int(fx), int(fy)), width)
            pygame.draw.circle(screen, YELLOW, (int(fx), int(fy)), int(width * 0.65))
            pygame.draw.circle( screen, WHITE, (int(fx), int(fy)), int(width * 0.35))

        flash_timer -= 1

    # HUD

    txt = font.render( f"SCORE {score}    LEVEL {level}", True, WHITE)

    screen.blit(txt, (20,20))

    pygame.display.flip()

pygame.quit()