# ==============================================================================
# FLAK-GAME — TEIL 1 (INITIALISIERUNG, SOUND-MANAGEMENT & BASIS)
# ==============================================================================
import pygame
import math
import random
import os
import sys

pygame.init()
pygame.mixer.init()

# Sicherer Basispfad für alle Assets (Doppelklick-Schutz)
BASE = os.path.dirname(os.path.abspath(__file__))

# --- Globaler Feuermodus ---
fire_mode = "short"

# --- Sound-Management mit maximaler Crash-Sicherung ---
explosion_sound = None
shot_sound = None
fernfeuer_sound = None  # Neuer Sound-Slot für das Fernfeuer
flieger_sound = None
mg_sound = None
click_sound = None
rotate_channel = None
pitch_channel = None

try:
    if os.path.exists(os.path.join(BASE, "whoosh.mp3")):
        explosion_sound = pygame.mixer.Sound(os.path.join(BASE, "whoosh.mp3"))
        explosion_sound.set_volume(1.0)
except: pass

try:
    if os.path.exists(os.path.join(BASE, "flak2.wav")):
        shot_sound = pygame.mixer.Sound(os.path.join(BASE, "flak2.wav"))
        shot_sound.set_volume(0.8)
except: pass

try:
    if os.path.exists(os.path.join(BASE, "flak1.wav")):
        fernfeuer_sound = pygame.mixer.Sound(os.path.join(BASE, "flak1.wav"))
        fernfeuer_sound.set_volume(0.3)  # Kraftvolle Lautstärke für das Fernfeuer
except: pass

try:
    if os.path.exists(os.path.join(BASE, "flugzeug2.mp3")):
        flieger_sound = pygame.mixer.Sound(os.path.join(BASE, "flugzeug2.mp3"))
        flieger_sound.set_volume(1.0)
except: pass

try:
    if os.path.exists(os.path.join(BASE, "return-fire2.mp3")):
        mg_sound = pygame.mixer.Sound(os.path.join(BASE, "return-fire2.mp3"))
        mg_sound.set_volume(0.5)
except: pass

try:
    if os.path.exists(os.path.join(BASE, "click.wav")):
        click_sound = pygame.mixer.Sound(os.path.join(BASE, "click.wav"))
        click_sound.set_volume(0.6)
except: pass

try:
    rotate_sound = pygame.mixer.Sound(os.path.join(BASE, "rad1.mp3"))
    rotate_sound.set_volume(0.5)
    rotate_channel = pygame.mixer.Channel(5)
    rotate_channel.play(rotate_sound, loops=-1)
except:
    rotate_channel = None

try:
    pitch_sound = pygame.mixer.Sound(os.path.join(BASE, "squeak1.mp3"))
    pitch_sound.set_volume(0.2)
    pitch_channel = pygame.mixer.Channel(6)
    pitch_channel.play(pitch_sound, loops=-1)
except:
    pitch_channel = None


# --- Bildschirm-Einstellungen ---
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("BLITZ - Heavy Flak 360")
clock = pygame.time.Clock()

# --- Farbpaletten ---
SKY1 = (120, 190, 255)
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


# ==============================================================================
# FLAK-GAME — TEIL 2 (SPIELVARIABLEN, HUD-SCHRIFTEN & ANGRIFFS-SETUPS)
# ==============================================================================

# --- Globale mathematische Hilfsfunktion ---
def get_3d_projection(world_angle, distance, altitude, player_yaw, player_pitch):
    rel_angle = world_angle - player_yaw
    while rel_angle > math.pi: rel_angle -= math.tau
    while rel_angle < -math.pi: rel_angle += math.tau

    horizontal_fov = 1.4
    if abs(rel_angle) > horizontal_fov / 2:
        return 0, 0, 0, False

    screen_x = (WIDTH // 2) + (rel_angle / (horizontal_fov / 2)) * (WIDTH // 2)
    horizon_y = HEIGHT // 2 + player_pitch * 300
    screen_y = horizon_y - altitude * (600 / distance)
    scale = 600 / distance
    return int(screen_x), int(screen_y), scale, True

# --- Spieler- & Geschützsteuerung ---
player_yaw = 0.0        # Aktueller horizontaler Blickwinkel (Bogenmaß)
player_pitch = 0.3      # Aktueller vertikaler Blickwinkel
target_yaw = 0.0        # Gewünschter Blickwinkel (für weiche Dämpfung)
target_pitch = 0.3      # Gewünschter Höhenwinkel
yaw_speed = 0.0         # Drehgeschwindigkeit für die Soundlautstärke

# --- Listen für Spielelemente ---
planes = []
shells = []
explosions = []
smokes = []
clouds = []
attack_bullet_holes = []


# --- Gameplay-Werte ---
score = 0
level = 1
planes_passed = 0
kills = 0               # Zählt die exakten Abschüsse für das HUD
spawn_timer = 30
game_mode = "flak"      # "flak" (Standard) oder "attack" (Jäger-Sturmangriff)

# --- Schuss- und Rückstoß-System ---
fire_delay = 0
next_barrel = 0         # 0 = Links, 1 = Rechts
left_recoil = 0
right_recoil = 0
flash_timer = 0
flash_barrel = 0
muzzle_positions = []


# --- Initialisierung der Schriftarten ---
try:
    font = pygame.font.SysFont("consolas", 22, bold=True)
    font_bold = pygame.font.SysFont("consolas", 24, bold=True)
    font_normal = pygame.font.SysFont("consolas", 24, bold=False)
    font_large = pygame.font.SysFont("consolas", 46, bold=True)   # Für die 4 großen Nullen
    font_small = pygame.font.SysFont("consolas", 22, bold=True)   # "Kills" / "Leaks"
except:
    font = pygame.font.Font(None, 24)
    font_bold = pygame.font.Font(None, 26)
    font_normal = pygame.font.Font(None, 26)
    font_large = pygame.font.Font(None, 48)
    font_small = pygame.font.Font(None, 24)                       


# --- Variablen für den Jäger-Sturmangriff ("attack") ---
attack_shadow_y = HEIGHT + 500
attack_from_left = True
attack_burst_active = False
attack_shoot_timer = 0
attack_shots_remaining = 0
attack_shadow_active = False
attack_finished = False
attack_end_timer = 0



# ==============================================================================
# FLAK-GAME — TEIL 3: ENTITÄTS-KLASSE FÜR DIE FLUGZEUGE (PLANE) — MIT RAUCHFAHNE
# ==============================================================================

class Plane:
    """ Flugzeuge im 360-Grad Raum, die am Horizont kreisen """
    def __init__(self, zeppelin=False):
        self.zeppelin = zeppelin
        self.hp = 3 if zeppelin else 1
        self.max_hp = 3 if zeppelin else 1  # Merkt sich das maximale Leben
        self.world_angle = random.uniform(0, math.tau)
        self.distance = random.uniform(1400, 2200)
        self.altitude = random.randint(120, 250)
        self.speed = random.uniform(0.8, 1.8) 
        self.orbit_speed = random.choice([-0.0015, -0.001, 0.001, 0.0015])
        self.alive = True
        
        # Ein kleiner Zähler, damit der Rauch nicht in jedem Frame spawnt (Performance!)
        self.smoke_timer = 0

    def update(self):
        self.distance -= self.speed
        self.world_angle += self.orbit_speed
        if self.distance < 180:
            self.alive = False

        # --- DYNAMISCHE RAUCHFAHNE BEI BESCHÄDIGUNG ---
        if self.alive and self.hp < self.max_hp:
            self.smoke_timer += 1
            # Je schwerer der Schaden, desto dichter der Rauch (Intervall wird kürzer)
            smoke_interval = 8 if self.hp == 1 else 15
            
            if self.smoke_timer >= smoke_interval:
                self.smoke_timer = 0
                
                # Wir holen uns die aktuellen 2D-Bildschirmkoordinaten des Zeppelins
                # Wenn er im sichtbaren FOV ist, spawnen wir den Rauch direkt hinter ihm
                # Wir nutzen globale Variablen player_yaw/player_pitch, die in der Schleife laufen
                sx, sy, scale, visible = self.get_screen_pos(player_yaw, player_pitch)
                if visible:
                    # Wir fügen der globalen `smokes`-Liste eine neue Rauchwolke hinzu
                    # Leicht versetzt nach hinten (entgegen der Flugrichtung)
                    direction = 1 if self.orbit_speed > 0 else -1
                    offset_x = -30 * direction * scale
                    smokes.append(Smoke(sx + offset_x + random.randint(-5, 5), sy + random.randint(-5, 5)))

    def get_screen_pos(self, player_yaw, player_pitch):
        return get_3d_projection(self.world_angle, self.distance, self.altitude, player_yaw, player_pitch)

    def draw(self, player_yaw, player_pitch):
        sx, sy, scale, visible = self.get_screen_pos(player_yaw, player_pitch)
        if not visible: return

        direction = 1 if self.orbit_speed > 0 else -1
        
        if self.zeppelin:
            color = {3: DARK, 2: GRAY}.get(self.hp, RED)
            w = int(180 * scale)
            h = int(60 * scale)
            pygame.draw.ellipse(screen, color, (sx - w//2, sy - h//2, w, h))
            pygame.draw.rect(screen, DARK, (sx - int(20*scale), sy + int(14*scale), int(40*scale), int(18*scale)))
            pygame.draw.circle(screen, GRAY, (int(sx + 75 * direction * scale), int(sy)), max(1, int(5*scale)))
        else:
            pts = [
                (sx + 40 * direction * scale, sy), (sx + 20 * direction * scale, sy - 6 * scale),
                (sx - 10 * direction * scale, sy - 6 * scale), (sx - 25 * direction * scale, sy - 22 * scale),
                (sx - 40 * direction * scale, sy - 22 * scale), (sx - 18 * direction * scale, sy - 6 * scale),
                (sx - 60 * direction * scale, sy - 6 * scale), (sx - 68 * direction * scale, sy - 16 * scale),
                (sx - 75 * direction * scale, sy - 16 * scale), (sx - 75 * direction * scale, sy + 16 * scale),
                (sx - 68 * direction * scale, sy + 16 * scale), (sx - 60 * direction * scale, sy + 6 * scale),
                (sx - 18 * direction * scale, sy + 6 * scale), (sx - 40 * direction * scale, sy + 22 * scale),
                (sx - 25 * direction * scale, sy + 22 * scale), (sx - 10 * direction * scale, sy + 6 * scale),
                (sx + 20 * direction * scale, sy + 6 * scale)
            ]
            if len(pts) > 2:
                pygame.draw.polygon(screen, DARK, pts)
            pygame.draw.circle(screen, GRAY, (int(sx - 18 * direction * scale), int(sy - 18 * scale)), max(1, int(4*scale)))
            pygame.draw.circle(screen, GRAY, (int(sx - 18 * direction * scale), int(sy + 18 * scale)), max(1, int(4*scale)))


# ==============================================================================
# FLAK-GAME — TEIL 4: ENTITÄTS-KLASSE FÜR PROJEKTILE (SHELL)
# ==============================================================================

class Shell:
    """ Ein von der Flak abgefeuertes Projektil mit physikalisch korrekter Neigungs-Ballistik """
    def __init__(self, x, y, dx, dy, mode="short", current_pitch=0.3):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.mode = mode
        self.pitch_at_shot = current_pitch  # Merkt sich den Kanonenwinkel beim Abschuss
        
        self.start_x = x
        self.start_y = y
        self.state = "rising" 
        self.life = 11

        # --- SOUND-ABSPIELEN BEIM ABSCHUSS ---
        if self.mode == "long":
            if fernfeuer_sound:
                fernfeuer_sound.play()
        else:
            if shot_sound:
                shot_sound.play()

    def update(self):
        # --- LOGIK FÜR NAHFEUER ---
        if self.mode == "short":
            self.x += self.dx
            self.y += self.dy
            self.life -= 1
            
        # --- LOGIK FÜR FERNFEUER (NEIGUNGS-BALLISTIK) ---
        elif self.mode == "long":
            if self.state == "rising":
                self.x += self.dx
                self.y += self.dy
                
                moved_dist = math.hypot(self.x - self.start_x, self.y - self.start_y)
                if moved_dist >= 140: 
                    self.state = "falling"
                    horizon_y = HEIGHT // 2 + self.pitch_at_shot * 300
                    
                    if self.pitch_at_shot > 0.8:
                        self.target_detonation_y = horizon_y - random.randint(10, 45)
                    else:
                        self.target_detonation_y = horizon_y - random.randint(110, 240)

                    self.y = -40 
                    self.x = self.start_x + (self.dx * 15) + random.uniform(-15, 15)
                    self.dy = random.uniform(9, 13) 
                    self.dx = self.dx * 0.15 + random.uniform(-0.5, 0.5)

            elif self.state == "falling":
                self.y += self.dy
                self.x += self.dx
                self.dy += 0.2
                if self.y >= self.target_detonation_y:
                    self.life = 0

    def draw(self):
        if self.mode == "short":
            pygame.draw.line(screen, ORANGE, (self.x - self.dx * 2, self.y - self.dy * 2), (self.x, self.y), 2)
            pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), 4)
        elif self.mode == "long":
            if self.state == "rising":
                pygame.draw.line(screen, YELLOW, (self.x - self.dx, self.y - self.dy), (self.x, self.y), 2)
            elif self.state == "falling":
                pygame.draw.line(screen, (190, 80, 15), (self.x - self.dx * 0.4, self.y - self.dy * 0.4), (self.x, self.y), 1)
                pygame.draw.circle(screen, (240, 140, 35), (int(self.x), int(self.y)), 1)


# ==============================================================================
# FLAK-GAME — TEIL 5: EFFEKT-KLASSEN FÜR EXPLOSIONEN UND WELTDEKORATIONEN
# ==============================================================================

class Explosion:
    def __init__(self, world_angle, distance, altitude, is_shrapnel=False):
        self.world_angle = world_angle
        self.distance = distance
        self.altitude = altitude
        self.is_shrapnel = is_shrapnel
        
        # Schrapnell-Explosionen am Horizont sind kleiner, kompakter und dunkler
        if self.is_shrapnel:
            self.radius = 2
            self.ring = 1
            self.life = 18
        else:
            self.radius = 6
            self.ring = 2
            self.life = 30

        # --- DYNAMISCHE LAUTSTÄRKE ---
        if explosion_sound is not None:
            volume_factor = 1.0 - ((distance - 180) / (2200 - 180))
            volume_factor = max(0.0, min(1.0, volume_factor))
            
            base_vol = 0.2 if self.is_shrapnel else 0.5
            
            channel = explosion_sound.play()
            if channel:
                channel.set_volume(base_vol * volume_factor)

    def update(self):
        if self.is_shrapnel:
            self.radius += 1.5  
            self.ring += 3.0
        else:
            self.radius += 4.5
            self.ring += 7.5
        self.life -= 1

    def draw(self, player_yaw, player_pitch):
        sx, sy, scale, visible = get_3d_projection(self.world_angle, self.distance, self.altitude, player_yaw, player_pitch)
        if not visible:
            return

        r = self.radius * scale
        rg = self.ring * scale

        if self.is_shrapnel:
            # SCHRAPNELL-OPTIK: Kleine, dünkler graue Rauchwölkchen statt massivem Feuer
            pygame.draw.circle(screen, (100, 100, 100), (int(sx), int(sy)), max(1, int(r)))
            pygame.draw.circle(screen, (60, 60, 60), (int(sx), int(sy)), max(1, int(r * 0.6)))
            if rg > 1:
                pygame.draw.circle(screen, (80, 80, 80), (int(sx), int(sy)), int(rg), max(1, int(1 * scale)))
        else:
            # INNERER BLITZ (Standard- & Flugzeugexplosion)
            pygame.draw.circle(screen, ORANGE, (int(sx), int(sy)), max(1, int(r)))
            pygame.draw.circle(screen, YELLOW, (int(sx), int(sy)), max(1, int(r * 0.55)))

            # DRUCKWELLE
            if rg > 1:
                pygame.draw.circle(screen, (235, 235, 235), (int(sx), int(sy)), int(rg), max(1, int(3 * scale)))
                pygame.draw.circle(screen, (160, 160, 160), (int(sx), int(sy)), int(rg * 1.25), max(1, int(2 * scale)))
                pygame.draw.circle(screen, (90, 90, 90), (int(sx), int(sy)), int(rg * 1.6), 1)


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


class Cloud:
    def __init__(self):
        self.world_angle = random.uniform(0, math.tau)
        self.distance = random.uniform(2500, 4000) 
        self.altitude = random.uniform(300, 600)   
        self.width = random.randint(150, 300)
        self.height = random.randint(40, 80)

    def draw(self, player_yaw, player_pitch):
        sx, sy, scale, visible = get_3d_projection(self.world_angle, self.distance, self.altitude, player_yaw, player_pitch)
        if not visible:
            return

        w = int(self.width * scale)
        h = int(self.height * scale)
        
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
        for crack in self.cracks:
            for start, end in crack:
                pygame.draw.line(surface, (0, 0, 0), start, end, 2)

        pygame.draw.circle(surface, (40, 40, 40), (self.x, self.y), 32)
        pygame.draw.circle(surface, (120, 120, 120), (self.x, self.y), 26)
        pygame.draw.circle(surface, SKY1, (self.x, self.y), 24)


# ==============================================================================
# FLAK-GAME — TEIL 6: SYSTEMFUNKTIONEN, HUD-SYSTEM & GESCHÜTZ-GEOMETRIE
# ==============================================================================

def reset_game():
    global score, level, planes_passed, clouds, kills
    planes.clear()
    shells.clear()
    explosions.clear()
    smokes.clear()
    attack_bullet_holes.clear()
    score = 0
    level = 1
    planes_passed = 0
    kills = 0                           
    clouds = [Cloud() for _ in range(15)]


def draw_fire_mode_hud(surface, f_bold, f_normal, current_mode):
    """ Rendert nur noch [SHORT] und [LONG] links und rechts neben dem Radar """
    text_short = "[SHORT]" if current_mode == "short" else "[Short]"
    color_short = GREEN if current_mode == "short" else LIGHT
    surface.blit(f_bold.render(text_short, True, color_short), (WIDTH // 2 - 220, HEIGHT - 45))

    text_long = "[LONG]" if current_mode == "long" else "[Long]"
    color_long = GREEN if current_mode == "long" else LIGHT
    surface.blit(f_bold.render(text_long, True, color_long), (WIDTH // 2 + 130, HEIGHT - 45))


def draw_flak_guns():
    """ Berechnet und rendert das massive Flakgeschütz im Vordergrund """
    global muzzle_positions, left_recoil, right_recoil

    elev = math.sin(player_pitch) * 560

    left_recoil *= 0.82
    right_recoil *= 0.82
    if left_recoil < 0.5: left_recoil = 0
    if right_recoil < 0.5: right_recoil = 0

    left_bx, left_by = -40, HEIGHT + 180
    right_bx, right_by = WIDTH + 40, HEIGHT + 180

    center_x = WIDTH // 2
    center_y = HEIGHT - elev - 180
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
            nx, ny = dx / dist, dy / dist
        else:
            nx, ny = 0, -1

        ex = bx + dx * 0.80 - nx * recoil_amount
        ey = by + dy * 0.80 - ny * recoil_amount

        muzzle_positions.append((ex, ey, tx, ty))

        base_width = 130
        muzzle_width = 16

        pygame.draw.polygon(screen, GRAY, [
            (bx - base_width, by), (bx + base_width, by),
            (ex + muzzle_width, ey), (ex - muzzle_width, ey)
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

    screen.fill(SKY1) 
    horizon_y = int(HEIGHT // 2 + player_pitch * 300)

    if horizon_y < HEIGHT:
        pygame.draw.rect(screen, SEA, (0, horizon_y, WIDTH, HEIGHT - horizon_y))

    shadow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    if attack_shadow_active:
        if attack_from_left:
            points = [
                (-500, attack_shadow_y + 300), (WIDTH // 3, attack_shadow_y + 100),
                (WIDTH + 500, horizon_y), (WIDTH + 500, attack_shadow_y - HEIGHT - 600),
                (WIDTH // 2, attack_shadow_y - HEIGHT - 300), (-500, attack_shadow_y - HEIGHT // 2)
            ]
        else:
            points = [
                (WIDTH + 500, attack_shadow_y + 300), (WIDTH - WIDTH // 3, attack_shadow_y + 100),
                (-500, horizon_y), (-500, attack_shadow_y - HEIGHT - 600),
                (WIDTH - WIDTH // 2, attack_shadow_y - HEIGHT - 300), (WIDTH + 500, attack_shadow_y - HEIGHT // 2)
            ]

        pygame.draw.polygon(shadow, (0, 0, 0, 140), points)
        attack_shadow_y -= 20

    screen.blit(shadow, (0, 0))

    if attack_shadow_active and not attack_burst_active and attack_shadow_y < horizon_y:
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


# ==============================================================================
# FLAK-GAME — TEIL 7: HAUPTSCHLEIFE & SPIEL-MODI
# ==============================================================================

# --- INITIALISIERUNG VOR DER SCHLEIFE ---
clouds = [Cloud() for _ in range(15)]
running = True

while running:
    current_time = pygame.time.get_ticks()

    # --- MODUS 1: JÄGER-STURMANGRIFF ("ATTACK") ---
    if game_mode == "attack":
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_w:
                    fire_mode = "long" if fire_mode == "short" else "short"
                    if click_sound: click_sound.play()

        dt = clock.tick(60)
        
        screen.fill(SKY1)
        horizon_y = int(HEIGHT // 2 + player_pitch * 300)
        if horizon_y < HEIGHT:
            pygame.draw.rect(screen, SEA, (0, horizon_y, WIDTH, HEIGHT - horizon_y))
            
        for c in clouds: c.draw(player_yaw, player_pitch)

        update_plane_attack()
        draw_flak_guns()
        
        for hole in attack_bullet_holes:
            hole.draw(screen)
            
        draw_fire_mode_hud(screen, font_bold, font_normal, fire_mode)
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
            elif event.key == pygame.K_w:
                fire_mode = "long" if fire_mode == "short" else "short"
                if click_sound: click_sound.play()

    keys = pygame.key.get_pressed()

    # Spawnsystem
    spawn_timer -= 1
    if spawn_timer <= 0 and len(planes) < 2:
        zepp = False
        if level >= 2 and random.random() < 0.25:
            zepp = True
        planes.append(Plane(zepp))
        spawn_timer = random.randint(40, 250)

    # Drehung und Höhenverstellung über Pfeiltasten
    if keys[pygame.K_LEFT]:    target_yaw -= 0.035
    if keys[pygame.K_RIGHT]:   target_yaw += 0.035
    if keys[pygame.K_UP]:      target_pitch += 0.015
    if keys[pygame.K_DOWN]:    target_pitch -= 0.015

    target_pitch = max(-0.05, min(1.45, target_pitch))
    
    player_yaw += (target_yaw - player_yaw) * 0.12
    player_pitch += (target_pitch - player_pitch) * 0.12
    yaw_speed = (target_yaw - player_yaw) * 0.12

    # Dynamische Getriebe-Geräusche
    if pitch_channel:
        pitch_speed = (target_pitch - player_pitch) * 0.12
        if abs(pitch_speed) > 0.0005:
            pitch_channel.set_volume(min(0.45, abs(pitch_speed) * 30.0))
        else:
            pitch_channel.set_volume(0.0)

    if rotate_channel:
        if abs(yaw_speed) > 0.0005:
            rotate_channel.set_volume(min(0.55, abs(yaw_speed) * 12.0))
        else:
            rotate_channel.set_volume(0.0)


# ==============================================================================
# FLAK-GAME — TEIL 8: SCHUSS- & KOLLISIONSLOGIK, RADAR UND FINALES RENDERING
# ==============================================================================

    fire_delay -= 1

    # Schießen mit Leertaste (Abwechselnd links / rechts) — DEIN ORIGINALES DAUERFEUER
    if keys[pygame.K_SPACE]:
        if fire_delay <= 0 and len(muzzle_positions) == 2:
            mx, my, tx, ty = muzzle_positions[next_barrel]
            dx, dy = tx - mx, ty - my
            dist = math.hypot(dx, dy)

            if dist != 0:
                dx /= dist
                dy /= dist

            speed = 26 if fire_mode == "short" else 22
            shells.append(Shell(mx, my, dx * speed, dy * speed, mode=fire_mode, current_pitch=player_pitch))

            for i in range(6):
                smokes.append(Smoke(mx + random.randint(-12, 12), my + random.randint(-12, 12)))

            if next_barrel == 0: left_recoil = 80
            else: right_recoil = 80

            flash_timer = 3
            flash_barrel = next_barrel
            next_barrel = 1 - next_barrel
            fire_delay = 6

    # Update Flugzeuge & Durchbruchsprüfung
    for p in planes[:]:
        p.update()
        if p.distance < 200:
            planes_passed += 1
            if p in planes: planes.remove(p)
            if planes_passed >= 5 and game_mode == "flak":
                start_plane_attack()

    # --- PROJEKTILE & KOLLISIONS-MECHANIK ---
    for s in shells[:]:
        if s.life <= 0:
            if s.mode == "long" and getattr(s, "state", "") == "falling":
                est_distance = random.uniform(1600, 2000)
                rel_x = (s.x - (WIDTH // 2)) / (WIDTH // 2)
                est_angle = player_yaw + (rel_x * 0.7)
                horizon_y = HEIGHT // 2 + player_pitch * 300
                est_altitude = (horizon_y - s.y) * (est_distance / 600)

                # Schrapnell-Rauchwolke (Dunkel) erzeugen am exakten 2D-Punkt der Kugel
                explosions.append(Explosion(est_angle, est_distance, est_altitude, is_shrapnel=True))

                # FIX: Kollisionsradius auf dem 2D-Bildschirm definieren (in Pixeln)
                # Jedes Flugzeug, das optisch in diesem Radius liegt, wird erfasst!
                shrapnel_screen_radius = 110  
                
                for p in planes[:]:
                    px, py, p_scale, p_visible = p.get_screen_pos(player_yaw, player_pitch)
                    if p_visible:
                        # Berechne den echten Pixelabstand zwischen Granaten-Detonation (s.x, s.y) und Flugzeug (px, py)
                        screen_dist = math.hypot(s.x - px, s.y - py)
                        
                        # Skaliert den Radius mit der Flugzeuggröße (weiter hinten = kleinerer Trefferradius)
                        if screen_dist < (shrapnel_screen_radius * p_scale):
                            score += 200 if p.zeppelin else 100
                            p.hp -= 1
                            
                            # FLUGZEUG-EXPLOSION: Mit innerem Blitz (is_shrapnel=False) direkt am Flugzeug!
                            explosions.append(Explosion(p.world_angle, p.distance, p.altitude, is_shrapnel=False))
                            
                            if p.hp <= 0:
                                if p in planes: planes.remove(p)
                                kills += 1  # Abschuss im Fernfeuer registriert
                            break

            if s in shells: 
                shells.remove(s)
            continue

        s.update()  

        if s.mode == "short":
            for p in planes[:]:
                sx, sy, scale, visible = p.get_screen_pos(player_yaw, player_pitch)
                if visible:
                    dist = math.hypot(s.x - sx, s.y - sy)
                    radius = 70 * scale if p.zeppelin else 35 * scale

                    if dist < max(15, radius):
                        # Nahfeuer-Trefferexplosion (Ebenfalls innerer Blitz)
                        explosions.append(Explosion(p.world_angle, p.distance, p.altitude, is_shrapnel=False))
                        score += 200 if p.zeppelin else 100
                        p.hp -= 1
                        if p.hp <= 0:
                            if p in planes: planes.remove(p)
                            kills += 1  # Abschuss im Nahfeuer registriert
                        if s in shells: shells.remove(s)
                        break

        if s in shells:
            if s.x < -100 or s.x > WIDTH + 100 or s.y < -100 or s.y > HEIGHT + 150:
                shells.remove(s)

    for e in explosions[:]:
        e.update()
        if e.life <= 0 and e in explosions: explosions.remove(e)

    for sm in smokes[:]:
        sm.update()
        if sm.life <= 0 and sm in smokes: smokes.remove(sm)

    # Levelberechnung läuft unsichtbar im Hintergrund weiter
    level = 1 + score // 1200

    # --- RENDERING WELTSCHICHTEN ---
    screen.fill(SKY1)

    for c in clouds: 
        c.draw(player_yaw, player_pitch)

    horizon_y = int(HEIGHT // 2 + player_pitch * 300)
    if horizon_y < HEIGHT:
        pygame.draw.rect(screen, SEA, (0, horizon_y, WIDTH, HEIGHT - horizon_y))

    for p in planes: p.draw(player_yaw, player_pitch)
    for e in explosions: e.draw(player_yaw, player_pitch)
    for sm in smokes: sm.draw()
    for s in shells: s.draw()

    # --- RADAR ---
    radar_x, radar_y = WIDTH // 2, HEIGHT - 90
    pygame.draw.circle(screen, DARK, (radar_x, radar_y), 80)
    pygame.draw.circle(screen, GREEN, (radar_x, radar_y), 75, 2)
    pygame.draw.circle(screen, GREEN, (radar_x, radar_y), 35, 1)

    left_fov_x = radar_x + math.sin(player_yaw - 0.7) * 75
    left_fov_y = radar_y - math.cos(player_yaw - 0.7) * 75
    right_fov_x = radar_x + math.sin(player_yaw + 0.7) * 75
    right_fov_y = radar_y - math.cos(player_yaw + 0.7) * 75
    pygame.draw.line(screen, (0, 100, 0), (radar_x, radar_y), (left_fov_x, left_fov_y), 1)
    pygame.draw.line(screen, (0, 100, 0), (radar_x, radar_y), (right_fov_x, right_fov_y), 1)
    pygame.draw.circle(screen, WHITE, (radar_x, radar_y), 3)

    for p in planes:
        r_dist = (p.distance / 2200.0) * 75
        rx = radar_x + int(math.sin(p.world_angle) * r_dist)
        ry = radar_y - int(math.cos(p.world_angle) * r_dist)
        pygame.draw.circle(screen, RED, (rx, ry), 4)

    draw_flak_guns()

    # --- DYNAMISCHES MÜNDUNGSFEUER ---
    if flash_timer > 0 and len(muzzle_positions) == 2:
        mx, my, tx, ty = muzzle_positions[flash_barrel]
        dx, dy = tx - mx, ty - my
        dist = math.hypot(dx, dy)
        if dist != 0:
            dx /= dist
            dy /= dist

        px, py = -dy, dx
        fx, fy = mx + dx * 60, my + dy * 60
        length, width = random.randint(70, 110), random.randint(18, 28)
        fire_scale = 1.0 if fire_mode == "short" else 0.65

        tip = (fx + dx * length * fire_scale, fy + dy * length * fire_scale)
        left = (fx + px * width * fire_scale, fy + py * width * fire_scale)
        right = (fx - px * width * fire_scale, fy - py * width * fire_scale)
        pygame.draw.polygon(screen, ORANGE, [left, tip, right])

        pygame.draw.circle(screen, ORANGE, (int(fx), int(fy)), int(width * fire_scale))
        pygame.draw.circle(screen, YELLOW, (int(fx), int(fy)), int(width * 0.65 * fire_scale))

    flash_timer -= 1

    for hole in attack_bullet_holes:
        hole.draw(screen)


    # --- BRANDNEUES HUD-SYSTEM (MIT TRANSPARENTEN HINTERGRUND-NULLEN) ---
    ALPHA_WHITE = (255, 255, 255)
    ALPHA_VAL = 100 

    # --- 1. LINKS OBEN: KILLS ---
    str_kills_real = str(kills)
    num_zeros_k = max(0, 4 - len(str_kills_real))
    
    surf_txt_k = font_small.render("Kills", True, ALPHA_WHITE)
    surf_txt_k.set_alpha(ALPHA_VAL) 
    
    surf_zeros_k = font_large.render("0" * num_zeros_k, True, ALPHA_WHITE)
    surf_zeros_k.set_alpha(ALPHA_VAL)
    surf_real_k = font_large.render(str_kills_real, True, WHITE)
    
    x_k = 30
    screen.blit(surf_zeros_k, (x_k, 20))
    screen.blit(surf_real_k, (x_k + surf_zeros_k.get_width(), 20))
    screen.blit(surf_txt_k, (x_k, 68))


    # --- 2. RECHTS OBEN: LEAKS ---
    str_leaks_real = str(planes_passed)
    num_zeros_d = max(0, 4 - len(str_leaks_real))
    
    surf_txt_d = font_small.render("Leaks", True, ALPHA_WHITE)
    surf_txt_d.set_alpha(ALPHA_VAL) 
    
    surf_zeros_d = font_large.render("0" * num_zeros_d, True, ALPHA_WHITE)
    surf_zeros_d.set_alpha(ALPHA_VAL)
    surf_real_d = font_large.render(str_leaks_real, True, WHITE)
    
    total_width_d = surf_zeros_d.get_width() + surf_real_d.get_width()
    x_d = WIDTH - total_width_d - 30
    
    screen.blit(surf_zeros_d, (x_d, 20))
    screen.blit(surf_real_d, (x_d + surf_zeros_d.get_width(), 20))
    screen.blit(surf_txt_d, (WIDTH - surf_txt_d.get_width() - 30, 68))

    draw_fire_mode_hud(screen, font_bold, font_normal, fire_mode)

    if planes_passed == 4:
        blink = (pygame.time.get_ticks() // 250) % 2
        if blink:
            alert_font = pygame.font.SysFont("consolas", 40, bold=True)
            alert = alert_font.render("!!! ALERT !!!", True, RED)
            alert.set_alpha(128)
            screen.blit(alert, alert.get_rect(center=(WIDTH // 2, 40)))

    pygame.display.flip()

pygame.quit()
sys.exit()


