# ==========================================
# Flak - TEIL 1: SETUP, VARIABLEN & MATHEMATIK
# ==========================================

import pygame
import math
import random
import os

pygame.init()
pygame.mixer.init()

BASE = os.path.dirname(os.path.abspath(__file__))

# --- Sound-Management (Crash-Sicherung) ---
try:
    explosion_sound = pygame.mixer.Sound(os.path.join(BASE, "whoosh.mp3"))
    explosion_sound.set_volume(1.0)
except:
    explosion_sound = None

try:
    # shot_sound = pygame.mixer.Sound(os.path.join(BASE, "mg-fire.mp3"))
    # shot_sound = pygame.mixer.Sound(os.path.join(BASE, "flak1.wav"))
    shot_sound = pygame.mixer.Sound(os.path.join(BASE, "flak2.wav"))
    # shot_sound = pygame.mixer.Sound(os.path.join(BASE, "flak4.mp3"))

    shot_sound.set_volume(0.8)
except:
    shot_sound = None

try:
    flieger_sound = pygame.mixer.Sound(os.path.join(BASE, "flugzeug2.mp3"))
    flieger_sound.set_volume(1.0)
except:
    flieger_sound = None

try:
    mg_sound = pygame.mixer.Sound(os.path.join(BASE, "return-fire2.mp3"))
    mg_sound.set_volume(0.5)
except:
    mg_sound = None

try:
    rotate_sound = pygame.mixer.Sound(os.path.join(BASE, "rad1.mp3")) # Geschütz drehen Sound
    rotate_sound.set_volume(0.7) # Startet stumm
    rotate_channel = pygame.mixer.Channel(5) # Ein fester Kanal für das dauerhafte Geräusch
    rotate_channel.play(rotate_sound, loops=-1) # Endlosschleife im Hintergrund
except:
    rotate_channel = None

try:
    pitch_sound = pygame.mixer.Sound(os.path.join(BASE, "squeak1.mp3")) # Geschütz schwenken Sound
    pitch_sound.set_volume(0.5) # Startet absolut lautlos
    pitch_channel = pygame.mixer.Channel(6) # Ein eigener, fester Soundkanal
    pitch_channel.play(pitch_sound, loops=-1) # Läuft unsichtbar im Hintergrund mit
except:
    pitch_channel = None


# --- Bildschirm-Einstellungen ---
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("BLITZ - Heavy Flak 360")

clock = pygame.time.Clock()

# --- Farbpaletten ---
SKY1 = (120, 190, 255)
SKY2 = (180, 220, 255)
SEA = (30, 70, 135)

DARK = (30, 30, 30)
GRAY = (100, 100, 100)
LIGHT = (170, 170, 170)
WHITE = (255, 255, 255)
GREEN = (0, 255, 60)

YELLOW = (255, 220, 80)
ORANGE = (255, 130, 40)
RED = (255, 50, 50)
SMOKE = (120, 120, 120)

# --- Globale mathematische Hilfsfunktion ---
def get_3d_projection(world_angle, distance, altitude, player_yaw, player_pitch):
    """ Berechnet aus Weltkoordinaten die 2D-Bildschirmposition und Skalierung """
    rel_angle = world_angle - player_yaw
    while rel_angle > math.pi: rel_angle -= math.tau
    while rel_angle < -math.pi: rel_angle += math.tau

    horizontal_fov = 1.4 # Sichtfeld des Spielers
    if abs(rel_angle) > horizontal_fov / 2:
        return 0, 0, 0, False

    screen_x = (WIDTH // 2) + (rel_angle / (horizontal_fov / 2)) * (WIDTH // 2)
    horizon_y = HEIGHT // 2 + player_pitch * 300
    screen_y = horizon_y - altitude * (600 / distance)
    scale = 600 / distance
    return int(screen_x), int(screen_y), scale, True


# ==========================================
# TEIL 2: SPIELE-KLASSEN & EFFEKTE
# ==========================================

class Plane:
    """ 
    Deine Original-Flugzeuge, angepasst für den 360-Grad-Raum.
    Sie spawnen im Kreis und fliegen quer durch das Sichtfeld des Schützen.
    """
    def __init__(self, zeppelin=False):
        self.zeppelin = zeppelin
        self.hp = 3 if zeppelin else 1
        
        # Flugzeuge starten in zufälliger Richtung im Raum (0 bis 360 Grad)
        self.world_angle = random.uniform(0, math.tau)
        # Distanz zur Flak (Weit weg am Horizont)
        self.distance = random.uniform(1400, 2200)
        # Echte Flughöhe
#         self.altitude = random.randint(150, 420)
        self.altitude = random.randint(120, 250)
        
        # Fluggeschwindigkeit (Annäherung)

        # self.speed = random.uniform(1.8, 3.2)
        self.speed = random.uniform(0.8, 1.8) 


        # Seitliche Flugbewegung (bestimmt, ob es von links nach rechts fliegt)

        # self.orbit_speed = random.choice([-0.0035, -0.002, 0.002, 0.0035])
        self.orbit_speed = random.choice([-0.0015, -0.001, 0.001, 0.0015])
        
        self.alive = True

    def update(self):
        # Das Flugzeug nähert sich und fliegt auf seiner Umlaufbahn
        self.distance -= self.speed
        self.world_angle += self.orbit_speed

        # Wenn es uns passiert hat
        if self.distance < 180:
            self.alive = False

    def get_screen_pos(self, player_yaw, player_pitch):
        """ Berechnet die 2D-Bildschirmposition basierend auf der 360°-Blickrichtung """
        return get_3d_projection(self.world_angle, self.distance, self.altitude, player_yaw, player_pitch)

    def draw(self, player_yaw, player_pitch):
        sx, sy, scale, visible = self.get_screen_pos(player_yaw, player_pitch)
        if not visible:
            return

        # Flugrichtung ermitteln für den Spiegel-Effekt (direction = 1 oder -1)
        direction = 1 if self.orbit_speed > 0 else -1
        
        if self.zeppelin:
            color = {3: DARK, 2: GRAY}.get(self.hp, RED)
            # Deine Original-Geometrie, perfekt skaliert für die Ferne/Nähe!
            w = int(180 * scale)
            h = int(60 * scale)
            pygame.draw.ellipse(screen, color, (sx - w//2, sy - h//2, w, h))
            pygame.draw.rect(screen, DARK, (sx - int(20*scale), sy + int(14*scale), int(40*scale), int(18*scale)))
            pygame.draw.circle(screen, GRAY, (int(sx + 75 * direction * scale), int(sy)), max(1, int(5*scale)))
        else:
            # Deine exakten Polygon-Punkte für den coolen Doppeldecker!
            pts = [
                (sx + 40 * direction * scale, sy),
                (sx + 20 * direction * scale, sy - 6 * scale),
                (sx - 10 * direction * scale, sy - 6 * scale),
                (sx - 25 * direction * scale, sy - 22 * scale),
                (sx - 40 * direction * scale, sy - 22 * scale),
                (sx - 18 * direction * scale, sy - 6 * scale),
                (sx - 60 * direction * scale, sy - 6 * scale),
                (sx - 68 * direction * scale, sy - 16 * scale),
                (sx - 75 * direction * scale, sy - 16 * scale),
                (sx - 75 * direction * scale, sy + 16 * scale),
                (sx - 68 * direction * scale, sy + 16 * scale),
                (sx - 60 * direction * scale, sy + 6 * scale),
                (sx - 18 * direction * scale, sy + 6 * scale),
                (sx - 40 * direction * scale, sy + 22 * scale),
                (sx - 25 * direction * scale, sy + 22 * scale),
                (sx - 10 * direction * scale, sy + 6 * scale),
                (sx + 20 * direction * scale, sy + 6 * scale),
            ]

            if len(pts) > 2:
                pygame.draw.polygon(screen, DARK, pts)
            # Motoren
            pygame.draw.circle(screen, GRAY, (int(sx - 18 * direction * scale), int(sy - 18 * scale)), max(1, int(4*scale)))
            pygame.draw.circle(screen, GRAY, (int(sx - 18 * direction * scale), int(sy + 18 * scale)), max(1, int(4*scale)))


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
        # Heller Schweif aus deinem Original-Code
        pygame.draw.line(screen, ORANGE, (self.x - self.dx * 2, self.y - self.dy * 2), (self.x, self.y), 2)
        pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), 4)


class Explosion:
    def __init__(self, world_angle, distance, altitude):
        self.world_angle = world_angle
        self.distance = distance
        self.altitude = altitude
        self.radius = 6
        self.ring = 2
        self.life = 30

        # --- DYNAMISCHE LAUTSTÄRKE HIER STARTEN ---
        if explosion_sound is not None:
            # Nahe am Spieler (180) -> Volle Lautstärke (Faktor 1.0)
            # Weit weg am Horizont (2200) -> Sehr leise/stumm (Faktor 0.0)
            volume_factor = 1.0 - ((distance - 180) / (2200 - 180))
            volume_factor = max(0.0, min(1.0, volume_factor)) # Verhindert Werte außerhalb von 0 und 1
            
            # Sound auf freiem Kanal abspielen und Lautstärke zuweisen
            channel = explosion_sound.play()
            if channel:
                channel.set_volume(0.5 * volume_factor) # 0.5 ist deine Basis-Lautstärke

    def update(self):
        self.radius += 4.5
        self.ring += 7.5
        self.life -= 1

    def draw(self, player_yaw, player_pitch):
        sx, sy, scale, visible = get_3d_projection(self.world_angle, self.distance, self.altitude, player_yaw, player_pitch)
        if not visible:
            return

        r = self.radius * scale
        rg = self.ring * scale

        # INNERER BLITZ
        pygame.draw.circle(screen, ORANGE, (int(sx), int(sy)), max(1, int(r)))
        pygame.draw.circle(screen, YELLOW, (int(sx), int(sy)), max(1, int(r * 0.55)))

        # DRUCKWELLE (Hauptimpuls)
        if rg > 1:
            pygame.draw.circle(screen, (235, 235, 235), (int(sx), int(sy)), int(rg), max(1, int(3 * scale)))
            pygame.draw.circle(screen, (160, 160, 160), (int(sx), int(sy)), int(rg * 1.25), max(1, int(2 * scale)))
            pygame.draw.circle(screen, (90, 90, 90), (int(sx), int(sy)), int(rg * 1.6), 1)

class Smoke:
    def __init__(self, x, y):
        # Mündungsrauch entsteht direkt im Vordergrund an den Mündungen
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


class Cloud:
    """ Wolken, die im 360-Grad-Raum stehen und die Drehung sichtbar machen """
    def __init__(self):
        self.world_angle = random.uniform(0, math.tau)
        self.distance = random.uniform(2500, 4000) # Sehr weit hinten im Hintergrund
        self.altitude = random.uniform(300, 600)   # Schön weit oben am Himmel
        self.width = random.randint(150, 300)
        self.height = random.randint(40, 80)

    def draw(self, player_yaw, player_pitch):
        # Nutzt unsere bewährte 3D-Projektion
        sx, sy, scale, visible = get_3d_projection(self.world_angle, self.distance, self.altitude, player_yaw, player_pitch)
        if not visible:
            return

        w = int(self.width * scale)
        h = int(self.height * scale)
        
        # Eine weiche, leicht transparente weiße Wolke zeichnen
        # Für Pygame ohne Alpha-Surface nutzen wir ein helles Grau/Weiß, das sich vom Himmel abhebt
        cloud_color = (235, 243, 255)
        pygame.draw.ellipse(screen, cloud_color, (sx - w//2, sy - h//2, w, h))
        pygame.draw.circle(screen, cloud_color, (sx, sy - h//4), int(h * 0.8))
        pygame.draw.circle(screen, cloud_color, (sx - w//4, sy), int(h * 0.7))
        pygame.draw.circle(screen, cloud_color, (sx + w//4, sy), int(h * 0.6))


class BulletHole:
    def __init__(self, pos):
        self.x, self.y = pos
        self.cracks = []
        crack_count = random.randint(6, 12)

        for _ in range(crack_count):
            angle = random.uniform(0, math.pi * 2)
            length = random.randint(20, 30)
            segments = []
            px, py = self.x, self.y

            for i in range(random.randint(4, 8)):
                angle += random.uniform(-0.4, 0.4)
                nx = px + math.cos(angle) * (length / 4)
                ny = py + math.sin(angle) * (length / 4)
                segments.append(((px, py), (nx, ny)))
                px, py = nx, ny

            self.cracks.append(segments)

    def draw(self, surface):
        # Schwarze Glasrisse zeichnen
        for crack in self.cracks:
            for start, end in crack:
                pygame.draw.line(surface, (0, 0, 0), start, end, 2)

        pygame.draw.circle(surface, (40, 40, 40), (self.x, self.y), 32)
        pygame.draw.circle(surface, (120, 120, 120), (self.x, self.y), 26)
        pygame.draw.circle(surface, SKY1, (self.x, self.y), 24)


# --- Globale Hilfsfunktionen ---


def reset_game():
    global score, level, planes_passed, clouds  # 'clouds' hier als global hinzufügen
    planes.clear()
    shells.clear()
    explosions.clear()
    smokes.clear()
    attack_bullet_holes.clear()
    score = 0
    level = 1
    planes_passed = 0

    # Weist den Wolken nun der globalen Spielliste zu
    clouds = [Cloud() for _ in range(15)]


# ==========================================
# TEIL 3A: STEUERUNGSFUNKTIONEN & INITIALISIERUNG
# ==========================================

def draw_flak_guns():
    global muzzle_positions, left_recoil, right_recoil

    # Nutzung des neuen player_pitch für die Höhensteuerung
    elev = math.sin(player_pitch) * 560

    # Rückstoß abbauen
    left_recoil *= 0.82
    right_recoil *= 0.82
    if left_recoil < 0.5: left_recoil = 0
    if right_recoil < 0.5: right_recoil = 0

    # Einzelne Werte statt Tupel-in-Tupel Verschachtelung
    left_bx, left_by = -40, HEIGHT + 180
    right_bx, right_by = WIDTH + 40, HEIGHT + 180

    center_x = WIDTH // 2
    center_y = HEIGHT - elev - 180
    
    # Trägheits-Offset sorgt für das Schwingen bei Bewegung
    # yaw_offset = yaw_speed * 1800
    yaw_offset = yaw_speed * 500


    left_target_x = center_x - 90 + yaw_offset
    right_target_x = center_x + 90 + yaw_offset

    barrel_info = [
        (left_bx, left_by, left_target_x, center_y),
        (right_bx, right_by, right_target_x, center_y)
    ]

    muzzle_positions = []

    for idx, (bx, by, tx, ty) in enumerate(barrel_info):
        recoil_amount = left_recoil if idx == 0 else right_recoil
        dx = tx - bx
        dy = ty - by
        dist = math.hypot(dx, dy)

        if dist > 0:
            nx = dx / dist
            ny = dy / dist
        else:
            nx, ny = 0, -1

        ex = bx + dx * 0.80 - nx * recoil_amount
        ey = by + dy * 0.80 - ny * recoil_amount

        muzzle_positions.append((ex, ey, tx, ty))

        base_width = 130
        muzzle_width = 16

        pygame.draw.polygon(screen, GRAY, [
            (bx - base_width, by),
            (bx + base_width, by),
            (ex + muzzle_width, ey),
            (ex - muzzle_width, ey)
        ])

        pygame.draw.line(screen, LIGHT, (bx - 36, by - 20), (ex - 4, ey - 5), 8)
        pygame.draw.line(screen, DARK, (bx + 28, by + 8), (ex + 5, ey + 4), 10)
        pygame.draw.line(screen, GRAY, (bx, by), (ex, ey), 32)
        pygame.draw.circle(screen, GRAY, (int(ex), int(ey)), muzzle_width)


def start_plane_attack():
    global game_mode, attack_shadow_y, attack_from_left
    global attack_burst_active, attack_shoot_timer, attack_shots_remaining, attack_shadow_active
    global attack_finished, attack_end_timer

    attack_finished = False
    attack_end_timer = 0
    attack_shadow_y = HEIGHT + 500
    attack_from_left = random.choice([True, False])
    attack_burst_active = False
    attack_shoot_timer = 0
    attack_shots_remaining = 0
    attack_shadow_active = True
    game_mode = "attack"

    if flieger_sound:
        flieger_sound.play()


def update_plane_attack():
    global game_mode, attack_shadow_y, attack_shadow_active
    global attack_burst_active, attack_shoot_timer, attack_shots_remaining
    global attack_finished, attack_end_timer

    shadow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    if attack_shadow_active:
        if attack_from_left:
            points = [
                (-500, attack_shadow_y + 300),
                (WIDTH // 3, attack_shadow_y + 100),
                (WIDTH + 500, attack_shadow_y - HEIGHT // 2),
                (WIDTH + 500, attack_shadow_y - HEIGHT - 600),
                (WIDTH // 2, attack_shadow_y - HEIGHT - 300),
                (-500, attack_shadow_y - HEIGHT // 2)
            ]
        else:
            points = [
                (WIDTH + 500, attack_shadow_y + 300),
                (WIDTH - WIDTH // 3, attack_shadow_y + 100),
                (-500, attack_shadow_y - HEIGHT // 2),
                (-500, attack_shadow_y - HEIGHT - 600),
                (WIDTH - WIDTH // 2, attack_shadow_y - HEIGHT - 300),
                (WIDTH + 500, attack_shadow_y - HEIGHT // 2)
            ]

        pygame.draw.polygon(shadow, (0, 0, 0, 140), points)
        attack_shadow_y -= 20

    screen.blit(shadow, (0, 0))

    if attack_shadow_active and not attack_burst_active and attack_shadow_y < HEIGHT // 2:
        attack_shadow_active = False
        attack_burst_active = True
        attack_shoot_timer = 0
        attack_shots_remaining = random.randint(3, 5)

        if mg_sound:
            mg_sound.play()

    if attack_burst_active:
        attack_shoot_timer += clock.get_time()
        while attack_shoot_timer > 80:
            attack_shoot_timer -= 80
            x = random.randint(50, WIDTH - 50)
            y = random.randint(50, HEIGHT // 3)

            attack_bullet_holes.append(BulletHole((x, y)))
            attack_shots_remaining -= 1

            if attack_shots_remaining <= 0:
                attack_burst_active = False
                attack_finished = True
                attack_end_timer = pygame.time.get_ticks()
                break

    for hole in attack_bullet_holes:
        hole.draw(screen)

    if attack_finished:
        elapsed = pygame.time.get_ticks() - attack_end_timer
        if elapsed > 1000:
            reset_game()
            game_mode = "flak"


# --- Spielvariablen Initialisierung ---
planes = []
shells = []
explosions = []
smokes = []
muzzle_positions = []
spawn_timer = 0
score = 0
level = 1
fire_delay = 0

clouds = [Cloud() for _ in range(15)]

# Neue Variablen für das stufenlose 360-Grad Ego-Spielfeld
player_yaw = 0.0          
player_pitch = 0.3        
target_yaw = 0.0
target_pitch = 0.3
yaw_speed = 0.0

left_recoil = 0
right_recoil = 0
next_barrel = 0
flash_timer = 0
flash_barrel = 0

planes_passed = 0
game_mode = "flak"
attack_mode = False

attack_shadow_y = HEIGHT + 500
attack_from_left = True
attack_burst_active = False
attack_shoot_timer = 0
attack_shots_remaining = 0
attack_shadow_active = False
attack_bullet_holes = []
attack_finished = False
attack_end_timer = 0

font = pygame.font.SysFont("consolas", 24)

# ==========================================
# TEIL 3B: MAIN GAME LOOP
# ==========================================

running = True

while running:
    # --- MODUS 1: JÄGER-STURMANGRIFF ("ATTACK") ---
    if game_mode == "attack":
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        dt = clock.tick(60)

        screen.fill(SKY1)

        pygame.draw.rect(screen, SEA, (0, HEIGHT // 2, WIDTH, HEIGHT // 2))

        radar_x = WIDTH // 2
        radar_y = HEIGHT - 90
        pygame.draw.circle(screen, DARK, (radar_x, radar_y), 85, 2)

        draw_flak_guns()
        update_plane_attack()
        pygame.display.flip()
        continue

    # --- MODUS 2: REINER ABWEHRMODUS ("FLAK") ---
    dt = clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    keys = pygame.key.get_pressed()

    # Spawnsystem
    spawn_timer -= 1
#     if spawn_timer <= 0 and len(planes) < 5:
    if spawn_timer <= 0 and len(planes) < 2:  # Anzahl der FLugzeuge

        zepp = False
        if level >= 3 and random.random() < 0.25:
            zepp = True
        planes.append(Plane(zepp))
        spawn_timer = random.randint(40, 250)

    # Drehung und Höhenverstellung über Pfeiltasten
    if keys[pygame.K_LEFT]:
        target_yaw -= 0.035
    if keys[pygame.K_RIGHT]:
        target_yaw += 0.035
    if keys[pygame.K_UP]:
        target_pitch += 0.015
    if keys[pygame.K_DOWN]:
        target_pitch -= 0.015

    # Logische Grenzen für den Nickwinkel
#     target_pitch = max(-0.05, min(1.2, target_pitch))
    target_pitch = max(-0.05, min(1.45, target_pitch))
    
    # Federleichte Trägheits-Dämpfung
    player_yaw += (target_yaw - player_yaw) * 0.12
    player_pitch += (target_pitch - player_pitch) * 0.12
    yaw_speed = (target_yaw - player_yaw) * 0.12

    # Dynamische Lautstärke für das Quietschen der Höhenverstellung (Pitch)
    if pitch_channel:
        # Wir berechnen, wie stark sich der Pitch in diesem Frame verändert
        pitch_speed = (target_pitch - player_pitch) * 0.12
        
        # Wenn sich die Rohre bewegen, drehen wir den Sound auf. 
        # Je schneller die Bewegung, desto lauter das Quietschen (maximal 0.35 Lautstärke)
        if abs(pitch_speed) > 0.001:
            current_volume = min(0.35, abs(pitch_speed) * 25.0)
            pitch_channel.set_volume(current_volume)
        else:
            # Wenn die Rohre stillstehen, blenden wir das Quietschen sofort aus
            pitch_channel.set_volume(0.0)


    # Dynamische Lautstärke für das Quietschen basierend auf der Drehgeschwindigkeit
    if rotate_channel:
        volume = min(0.4, abs(yaw_speed) * 8.0) # Je schneller die Drehung, desto lauter das Quietschen
        rotate_channel.set_volume(volume)

    fire_delay -= 1

    # Schießen mit Leertaste (Abwechselnd links / rechts)
    if keys[pygame.K_SPACE]:
        if fire_delay <= 0 and len(muzzle_positions) == 2:
            if shot_sound:
                shot_sound.play()

            mx, my, tx, ty = muzzle_positions[next_barrel]
            dx = tx - mx
            dy = ty - my
            dist = math.hypot(dx, dy)

            if dist != 0:
                dx /= dist
                dy /= dist

            speed = 26
            shells.append(Shell(mx, my, dx * speed, dy * speed))

            for i in range(6):
                smokes.append(Smoke(mx + random.randint(-12, 12), my + random.randint(-12, 12)))

            if next_barrel == 0:
                left_recoil = 80
            else:
                right_recoil = 80

            flash_timer = 3
            flash_barrel = next_barrel
            next_barrel = 1 - next_barrel
            fire_delay = 6

    # Update Flugzeuge & Durchbruchsprüfung
    for p in planes[:]:
        p.update()

        # Flugzeug im 3D-Raum bricht durch die Verteidigungslinie
        if p.distance < 200:
            planes_passed += 1
            if p in planes:
                planes.remove(p)

            if planes_passed >= 5 and game_mode == "flak":
                start_plane_attack()


    # Projektile aktualisieren & Kollisionsprüfung auf dem Bildschirm
    for s in shells[:]:
        s.update()  # WICHTIG: Das sorgt dafür, dass die Geschosse fliegen!

        # 1. Kollisionsprüfung mit den Flugzeugen
        for p in planes[:]:
            sx, sy, scale, visible = p.get_screen_pos(player_yaw, player_pitch)
            if visible:
                dist = math.hypot(s.x - sx, s.y - sy)
                radius = 70 * scale if p.zeppelin else 35 * scale

                if dist < max(15, radius):
                    # Erzeugt 3D Explosion am Flugzeugort (spielt den Sound automatisch distanzbasiert ab!)
                    explosions.append(Explosion(p.world_angle, p.distance, p.altitude))

                    score += 200 if p.zeppelin else 100
                    p.hp -= 1

                    if p.hp <= 0 and p in planes:
                        planes.remove(p)

                    if s in shells:
                        shells.remove(s)
                    break  # Bricht die Flugzeug-Schleife ab, da das Geschoss getroffen hat

        # 2. Prüfen, ob das Geschoss den Bildschirm verlassen hat oder verglüht ist
        # (Nur prüfen, wenn es nicht schon durch einen Treffer oben gelöscht wurde)
        if s in shells:
            if s.life <= 0 or s.x < -100 or s.x > WIDTH + 100 or s.y < -100:
                shells.remove(s)

    # Explosionen aktualisieren
    for e in explosions[:]:
        e.update()
        if e.life <= 0 and e in explosions:
            explosions.remove(e)

    # Rauch aktualisieren
    for s in smokes[:]:
        s.update()
        if s.life <= 0 and s in smokes:
            smokes.remove(s)

    level = 1 + score // 1200

    # RENDERING DER WELTSCHICHTEN
    screen.fill(SKY1)

    for c in clouds: c.draw(player_yaw, player_pitch)

    horizon_y = int(HEIGHT // 2 + player_pitch * 300)
    if horizon_y < HEIGHT:
        pygame.draw.rect(screen, SEA, (0, horizon_y, WIDTH, HEIGHT - horizon_y))

    # 3D Weltelemente zeichnen
    for p in planes: p.draw(player_yaw, player_pitch)
    for e in explosions: e.draw(player_yaw, player_pitch)
    for s in smokes: s.draw()
    for s in shells: s.draw()

    # RADAR UNTEN IN DER MITTE (360 Grad Draufsicht)
    radar_x = WIDTH // 2
    radar_y = HEIGHT - 90
    pygame.draw.circle(screen, DARK, (radar_x, radar_y), 80)
    pygame.draw.circle(screen, GREEN, (radar_x, radar_y), 75, 2)
    pygame.draw.circle(screen, GREEN, (radar_x, radar_y), 35, 1)

    # Sichtkonus Linien
    left_fov_x = radar_x + math.sin(player_yaw - 0.7) * 75
    left_fov_y = radar_y - math.cos(player_yaw - 0.7) * 75
    right_fov_x = radar_x + math.sin(player_yaw + 0.7) * 75
    right_fov_y = radar_y - math.cos(player_yaw + 0.7) * 75
    pygame.draw.line(screen, (0, 100, 0), (radar_x, radar_y), (left_fov_x, left_fov_y), 1)
    pygame.draw.line(screen, (0, 100, 0), (radar_x, radar_y), (right_fov_x, right_fov_y), 1)
    pygame.draw.circle(screen, WHITE, (radar_x, radar_y), 3)

    # Flugzeuge auf dem Radar punkten
    for p in planes:
        r_dist = (p.distance / 2200.0) * 75
        rx = radar_x + int(math.sin(p.world_angle) * r_dist)
        ry = radar_y - int(math.cos(p.world_angle) * r_dist)
        pygame.draw.circle(screen, RED, (rx, ry), 4)

    # Flak-Rohre zeichnen
    draw_flak_guns()

    # DYNAMISCHES MÜNDUNGSFEUER
    if flash_timer > 0 and len(muzzle_positions) == 2:
        mx, my, tx, ty = muzzle_positions[flash_barrel]

        dx = tx - mx
        dy = ty - my
        dist = math.hypot(dx, dy)

        if dist != 0:
            dx /= dist
            dy /= dist

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
        pygame.draw.polygon(screen, ORANGE, [left, tip, right])

        tip2 = (fx + dx * (length * 0.65), fy + dy * (length * 0.65))
        left2 = (fx + px * (width * 0.45), fy + py * (width * 0.45))
        right2 = (fx - px * (width * 0.45), fy - py * (width * 0.45))
        pygame.draw.polygon(screen, YELLOW, [left2, tip2, right2])

        tip3 = (fx + dx * (length * 0.35), fy + dy * (length * 0.35))
        left3 = (fx + px * (width * 0.18), fy + py * (width * 0.18))
        right3 = (fx - px * (width * 0.18), fy - py * (width * 0.18))
        pygame.draw.polygon(screen, WHITE, [left3, tip3, right3])

        pygame.draw.circle(screen, ORANGE, (int(fx), int(fy)), width)
        pygame.draw.circle(screen, YELLOW, (int(fx), int(fy)), int(width * 0.65))
        pygame.draw.circle(screen, WHITE, (int(fx), int(fy)), int(width * 0.35))

    flash_timer -= 1

    # Cockpit-Treffereffekte zeichnen
    for hole in attack_bullet_holes:
        hole.draw(screen)

    # Benutzeroberfläche & Alarm
    txt = font.render(f"SCORE {score}    LEVEL {level}", True, WHITE)

    if planes_passed == 4:
        blink = (pygame.time.get_ticks() // 250) % 2
        if blink:
            size = 160 + int(math.sin(pygame.time.get_ticks() * 0.01) * 15)
            alert_font = pygame.font.SysFont("consolas", size, bold=True)
            alert = alert_font.render("!!! ALERT !!!", True, RED)
            screen.blit(alert, alert.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

    screen.blit(txt, (20, 20))
    pygame.display.flip()

pygame.quit()


