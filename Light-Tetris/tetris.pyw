#
#     Leucht-Tetris
#

import pygame
import sys
import copy
import random
import os
import math

BASE = os.path.dirname(os.path.abspath(__file__))

pygame.init()
pygame.mixer.init()

width = 800
height = 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Leuchtstein-Tetris")
clock = pygame.time.Clock()

SOUND_VOLUME = 0.5  

sound_klick = None
sound_tok = None
sound_clear = None  # Umbenannt für den neuen Sound

print("--- Absoluter Pfad Sound-Check ---")
try:
    sound_klick = pygame.mixer.Sound(os.path.join(BASE, "klick.wav"))
    sound_klick.set_volume(SOUND_VOLUME)
except Exception as e:
    print(f"❌ Fehler bei 'klick.wav': {e}")

try:
    sound_tok = pygame.mixer.Sound(os.path.join(BASE, "tock.wav"))
    sound_tok.set_volume(SOUND_VOLUME)
except Exception as e:
    print(f"❌ Fehler bei 'tock.wav': {e}")

try:
    # Neu: boeh.wav statt schnapp.wav
    sound_clear = pygame.mixer.Sound(os.path.join(BASE, "clear.wav"))
    sound_clear.set_volume(0.8)  # Auf 0.3 eingestellt
except Exception as e:
    print(f"❌ Fehler bei 'boeh.wav': {e}")

CUBE_SIZE = 26  
GRID_COLS = 10
GRID_ROWS = 20

GRID_X_OFFSET = (width - (GRID_COLS * CUBE_SIZE)) // 2
GRID_Y_OFFSET = (height - (GRID_ROWS * CUBE_SIZE)) // 2

SHAPES = {
    'I': [(0, -1), (0, 0), (0, 1), (0, 2)],
    'O': [(0, 0), (1, 0), (0, 1), (1, 1)],
    'T': [(0, 0), (-1, 0), (1, 0), (0, -1)],
    'S': [(0, 0), (1, 0), (0, 1), (-1, 1)],
    'Z': [(0, 0), (-1, 0), (0, 1), (1, 1)],
    'J': [(0, 0), (0, -1), (0, 1), (-1, 1)],
    'L': [(0, 0), (0, -1), (0, 1), (1, 1)]
}


class GlowCube:
    def __init__(self, rel_x, rel_y, size=CUBE_SIZE):
        self.size = size
        self.rel_x = rel_x
        self.rel_y = rel_y
        
        # Visuelle Position
        self.current_cx = 0.0
        self.current_cy = 0.0
        
        # Kreisbahn-Werte
        self.radius = math.hypot(rel_x, rel_y) * size
        self.target_angle = math.atan2(rel_y, rel_x)
        self.current_angle = self.target_angle
        
        # --- NEU: Individuelle Rotationsgeschwindigkeit pro Würfel ---
        self.rotation_speed = 1.0  # Standardmäßig sofortiges Einrasten

    def update(self, center_x, center_y):
        # Basis-Zielposition auf dem Spielfeld
        target_cx = center_x + self.rel_x * self.size + self.size / 2
        target_cy = center_y + self.rel_y * self.size + self.size / 2
        
        if self.radius == 0:
            self.current_cx = target_cx
            self.current_cy = target_cy
            return

        # Kreisbahn-Differenz berechnen
        angle_diff = self.target_angle - self.current_angle
        angle_diff = (angle_diff + math.pi) % (2 * math.pi) - math.pi
        
        # Der Würfel nähert sich mit seiner spezifischen Geschwindigkeit an
        self.current_angle += angle_diff * self.rotation_speed

        # Position auf der Kreisbahn berechnen
        local_x = math.cos(self.current_angle) * self.radius
        local_y = math.sin(self.current_angle) * self.radius
        
        self.current_cx = center_x + self.size / 2 + local_x
        self.current_cy = center_y + self.size / 2 + local_y

    def draw(self, screen, is_next=False):
        draw_x = self.current_cx - self.size / 2
        draw_y = self.current_cy - self.size / 2

        if is_next:
            for i in range(6, 0, -2):
                g_surf = pygame.Surface((self.size + i * 2, self.size + i * 2), pygame.SRCALPHA)
                pygame.draw.rect(g_surf, (100, 100, 100, 8), g_surf.get_rect(), border_radius=4)
                screen.blit(g_surf, (draw_x - i, draw_y - i))
            pygame.draw.rect(screen, (110, 114, 120), (draw_x, draw_y, self.size, self.size), border_radius=3)
        else:
            # Unverändertes Original-Leuchten
            for i in range(12, 0, -2):
                alpha = int(20 * (1 - (i / 12)))
                glow_size = self.size + i * 2
                glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (255, 255, 255, alpha), glow_surf.get_rect(), border_radius=6)
                screen.blit(glow_surf, (draw_x - i, draw_y - i))
            pygame.draw.rect(screen, (255, 255, 255), (draw_x, draw_y, self.size, self.size), border_radius=3)


class Tetromino:
    def __init__(self, shape_type, grid_x=4, grid_y=1):
        self.shape_type = shape_type
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.cubes = [GlowCube(rx, ry) for rx, ry in SHAPES[shape_type]]
        
        cx, cy = self.get_absolute_center()
        for cube in self.cubes:
            cube.current_cx = cx + cube.rel_x * CUBE_SIZE + CUBE_SIZE / 2
            cube.current_cy = cy + cube.rel_y * CUBE_SIZE + CUBE_SIZE / 2

    def get_absolute_center(self):
        cx = GRID_X_OFFSET + self.grid_x * CUBE_SIZE
        cy = GRID_Y_OFFSET + self.grid_y * CUBE_SIZE
        return cx, cy

    def update(self):
        cx, cy = self.get_absolute_center()
        for cube in self.cubes:
            cube.update(cx, cy)

    def draw(self, screen, is_next=False):
        for cube in self.cubes:
            cube.draw(screen, is_next=is_next)

    def rotate(self, clockwise=True):
        if sound_klick:
            pygame.mixer.find_channel(True).play(sound_klick)
            
        for index, cube in enumerate(self.cubes):
            old_rx = cube.rel_x
            if clockwise:
                cube.rel_x = -cube.rel_y
                cube.rel_y = old_rx
                cube.target_angle += math.pi / 2
            else:
                cube.rel_x = cube.rel_y
                cube.rel_y = -old_rx
                cube.target_angle -= math.pi / 2
                
            # --- NEU: Zuweisung der Geschwindigkeiten ---
            if index == 3:
                cube.rotation_speed = 0.18  # Der vierte Würfel wandert gemütlich hinterher
            else:
                cube.rotation_speed = 1.0   # Die ersten 3 Würfel springen sofort ans Ziel
                cube.current_angle = cube.target_angle  # Erzwingt das sofortige visuelle Einrasten

    def get_occupied_cells(self, offset_x=0, offset_y=0):
        cells = []
        for cube in self.cubes:
            cells.append((self.grid_x + cube.rel_x + offset_x, self.grid_y + cube.rel_y + offset_y))
        return cells


# Klasse für das Hauptspiel (Grid, Spiellogik, Input)

class TetrisGame:
    def __init__(self):
        self.grid = [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        self.shape_pool = list(SHAPES.keys())
        
        self.current_piece = Tetromino(random.choice(self.shape_pool))
        self.next_piece_type = random.choice(self.shape_pool)
        self.preview_piece = Tetromino(self.next_piece_type)
        
        self.fall_time = 0
        self.fall_speed = 600  
        
        self.score = 0
        self.lines = 0
        
        self.lines_to_clear = []
        self.clear_animation_timer = 0
        self.clear_animation_duration = 400 
        self.game_over = False

    def check_collision(self, piece, offset_x=0, offset_y=0):
        for x, y in piece.get_occupied_cells(offset_x, offset_y):
            if x < 0 or x >= GRID_COLS or y >= GRID_ROWS:
                return True
            if gy := y >= 0 and self.grid[y][x] != 0:
                return True
        return False

    def lock_piece(self, play_sound=True):
        if play_sound and sound_tok:
            pygame.mixer.find_channel(True).play(sound_tok)
            
        for x, y in self.current_piece.get_occupied_cells():
            if y >= 0:
                self.grid[y][x] = 1
        
        self.check_for_lines()
        if not self.lines_to_clear:
            self.spawn_next_piece()

    def spawn_next_piece(self):
        self.current_piece = Tetromino(self.next_piece_type)
        self.next_piece_type = random.choice(self.shape_pool)
        self.preview_piece = Tetromino(self.next_piece_type)
        
        if self.check_collision(self.current_piece):
            self.game_over = True

    def check_for_lines(self):
        self.lines_to_clear = [r for r in range(GRID_ROWS) if all(self.grid[r][c] == 1 for c in range(GRID_COLS))]
        if self.lines_to_clear:
            self.clear_animation_timer = self.clear_animation_duration
            # Spielt nun boeh.wav ab
            if sound_clear:
                pygame.mixer.find_channel(True).play(sound_clear)

    def execute_line_clearing(self):
        num_lines = len(self.lines_to_clear)
        new_grid = [row for r, row in enumerate(self.grid) if r not in self.lines_to_clear]
        
        score_multiplier = {1: 100, 2: 300, 3: 500, 4: 800}
        self.score += score_multiplier.get(num_lines, 100)
        self.lines += num_lines
        
        for _ in range(num_lines):
            new_grid.insert(0, [0 for _ in range(GRID_COLS)])
        self.grid = new_grid
        self.lines_to_clear = []
        
        self.spawn_next_piece()

    def execute_hard_drop(self):
        if self.lines_to_clear or self.game_over:
            return
        
        # Zähler für die herabgefallenen Reihen
        dropped_rows = 0
        while not self.check_collision(self.current_piece, offset_y=1):
            self.current_piece.grid_y += 1
            dropped_rows += 1 # Jede Reihe mitzählen
            
        # 2 Punkte pro Reihe für den Hard Drop hinzufügen
        self.score += dropped_rows * 2
        
        if sound_tok:
            pygame.mixer.find_channel(True).play(sound_tok)
        self.lock_piece(play_sound=False)

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
                
            # JETZT HIER: Setzt das Spiel JEDERZEIT zurück (mitten im Spiel & bei Game Over)
            if event.key == pygame.K_r:
                self.__init__() 
                return

            if self.game_over:
                return

            if self.lines_to_clear: 
                return
                
            if event.key == pygame.K_LEFT:
                if not self.check_collision(self.current_piece, offset_x=-1):
                    self.current_piece.grid_x -= 1

            elif event.key == pygame.K_RIGHT:
                if not self.check_collision(self.current_piece, offset_x=1):
                    self.current_piece.grid_x += 1

            elif event.key == pygame.K_UP:  
                test_piece = copy.deepcopy(self.current_piece)
                test_piece.rotate(clockwise=True)
                if not self.check_collision(test_piece):
                    self.current_piece.rotate(clockwise=True)

            elif event.key == pygame.K_DOWN:  
                test_piece = copy.deepcopy(self.current_piece)
                test_piece.rotate(clockwise=False)
                if not self.check_collision(test_piece):
                    self.current_piece.rotate(clockwise=False)

            elif event.key == pygame.K_SPACE:  
                self.execute_hard_drop()

    def update(self, dt):
        if self.game_over:
            return

        if self.lines_to_clear:
            self.clear_animation_timer -= dt
            if self.clear_animation_timer <= 0:
                self.execute_line_clearing()
            return 

        # SLOW DROP / SOFT DROP LOGIK

        keys = pygame.key.get_pressed()
        is_soft_dropping = keys[pygame.K_s] # Prüfen, ob S gedrückt ist
        current_speed = 50 if is_soft_dropping else self.fall_speed
        
        self.fall_time += dt
        if self.fall_time >= current_speed:
            self.fall_time = 0
            if not self.check_collision(self.current_piece, offset_y=1):
                self.current_piece.grid_y += 1
                
                # Wenn aktiv die S-Taste gedrückt wurde, gibt es 1 Punkt
                if is_soft_dropping:
                    self.score += 1
            else:
                self.lock_piece(play_sound=True)
                
        self.current_piece.update()

        # Positionierung und Update des Vorschau-Steins
        preview_x = GRID_X_OFFSET + GRID_COLS * CUBE_SIZE + 80
        preview_y = GRID_Y_OFFSET + 60
        self.preview_piece.update()
        
        for cube in self.preview_piece.cubes:
            cube.current_cx = preview_x + cube.rel_x * CUBE_SIZE + CUBE_SIZE / 2
            cube.current_cy = preview_y + cube.rel_y * CUBE_SIZE + CUBE_SIZE / 2

    def draw(self, screen):
        # Hintergrund-Gitterlinien zeichnen
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                rect = pygame.Rect(GRID_X_OFFSET + c * CUBE_SIZE, GRID_Y_OFFSET + r * CUBE_SIZE, CUBE_SIZE, CUBE_SIZE)
                pygame.draw.rect(screen, (20, 20, 20), rect, 1)

        # Spielfeld/Grid zeichnen
        for r in range(GRID_ROWS):
            is_animating = r in self.lines_to_clear
            for c in range(GRID_COLS):
                if self.grid[r][c] == 1:
                    bx = GRID_X_OFFSET + c * CUBE_SIZE
                    by = GRID_Y_OFFSET + r * CUBE_SIZE
                    
                    if is_animating:
                        # DESIGN-ANPASSUNG: Extrem reduziertes, dezentes Leuchten (Alpha auf 10)
                        for i in range(8, 0, -2):
                            g_surf = pygame.Surface((CUBE_SIZE + i * 2, CUBE_SIZE + i * 2), pygame.SRCALPHA)
                            pygame.draw.rect(g_surf, (200, 200, 200, 10), g_surf.get_rect(), border_radius=4)
                            screen.blit(g_surf, (bx - i, by - i))

                        # Kern zu einem weichen Hellgrau gedimmt
                        pygame.draw.rect(screen, (180, 185, 190), (bx, by, CUBE_SIZE, CUBE_SIZE), border_radius=3)

                    else:
                        for i in range(6, 0, -2):
                            g_surf = pygame.Surface((CUBE_SIZE + i * 2, CUBE_SIZE + i * 2), pygame.SRCALPHA)
                            pygame.draw.rect(g_surf, (100, 100, 100, 8), g_surf.get_rect(), border_radius=4)
                            screen.blit(g_surf, (bx - i, by - i))
                        pygame.draw.rect(screen, (110, 114, 120), (bx, by, CUBE_SIZE, CUBE_SIZE), border_radius=3)

        # Aktiven Stein zeichnen
        if not self.game_over:
            self.current_piece.draw(screen)

        # UI Schriften initialisieren
        font_label = pygame.font.SysFont(None, 24)
        font_value = pygame.font.SysFont(None, 32)
        
        # NÄCHSTER STECK-BEREICH
        next_text = font_label.render("NEXT", True, (100, 100, 100))
        screen.blit(next_text, (GRID_X_OFFSET + GRID_COLS * CUBE_SIZE + 50, GRID_Y_OFFSET))
        
        # Übergibt das Flag an das Vorschaustück für abgedunkeltes Zeichnen
        self.preview_piece.draw(screen, is_next=True)

        # Seitliches Info-Panel (Punkte & Reihen)
        panel_x = GRID_X_OFFSET - 140
        
        score_label = font_label.render("SCORE", True, (100, 100, 100))
        score_num = font_value.render(str(self.score), True, (255, 255, 255))
        screen.blit(score_label, (panel_x, GRID_Y_OFFSET))
        screen.blit(score_num, (panel_x, GRID_Y_OFFSET + 25))
        
        lines_label = font_label.render("LINES", True, (100, 100, 100))
        lines_num = font_value.render(str(self.lines), True, (255, 255, 255))
        screen.blit(lines_label, (panel_x, GRID_Y_OFFSET + 100))
        screen.blit(lines_num, (panel_x, GRID_Y_OFFSET + 125))

        # Game Over Overlay
        if self.game_over:
            overlay = pygame.Surface((width, height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180)) 
            screen.blit(overlay, (0, 0))
            
            font_go = pygame.font.SysFont(None, 72)
            font_sub = pygame.font.SysFont(None, 28)
            
            go_text_glow = font_go.render("GAME OVER", True, (150, 150, 150))
            go_text = font_go.render("GAME OVER", True, (255, 255, 255))
            
            restart_text = font_sub.render("Press 'R' to Restart", True, (120, 120, 120))
            quit_text = font_sub.render("Press 'ESC' to Quit", True, (120, 120, 120))
            
            cx = width // 2
            cy = height // 2
            
            screen.blit(go_text_glow, (cx - go_text_glow.get_width() // 2 + 2, cy - 80 + 2))
            screen.blit(go_text, (cx - go_text.get_width() // 2, cy - 80))
            screen.blit(restart_text, (cx - restart_text.get_width() // 2, cy + 15))
            screen.blit(quit_text, (cx - quit_text.get_width() // 2, cy + 60))


# HAUPTSCHLEIFE

game = TetrisGame()

running = True
while running:
    dt = clock.tick(60)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        game.handle_input(event)

    game.update(dt)

    screen.fill((5, 5, 5))  
    game.draw(screen)
    pygame.display.flip()

pygame.quit()
sys.exit()

