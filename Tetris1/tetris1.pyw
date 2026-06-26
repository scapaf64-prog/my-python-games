import pygame
import random

# Initialisierung
pygame.init()
pygame.mixer.init()

line_clear_sound = pygame.mixer.Sound("kuhglocke1.mp3")
line_fall_sound = pygame.mixer.Sound("fall.ogg")

# Konstanten
BLOCK_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
SCREEN_WIDTH = BLOCK_SIZE * (GRID_WIDTH + 6)
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
        self.current_piece = self.new_piece()
        self.next_piece = self.new_piece()
        self.font = pygame.font.Font(None, 30)
        self.font_large = pygame.font.Font(None, 60)

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
        self.current_piece = self.next_piece
        self.next_piece = self.new_piece()
        if not self.valid_position(self.current_piece['shape'],
                                   self.current_piece['x'],
                                   self.current_piece['y']):
            self.game_over = True

    def clear_lines(self):
        lines_to_clear = []
        for y in range(GRID_HEIGHT):
            if all(self.grid[y]):
                lines_to_clear.append(y)
      
        cleared = len(lines_to_clear)
        if cleared:
            self.draw()
            pygame.time.delay(200)
            line_clear_sound.play()

            self.draw_line_clear_animation(lines_to_clear)

            for y in lines_to_clear:
                del self.grid[y]
                self.grid.insert(0, [0] * GRID_WIDTH)

            points = [0, 100, 300, 500, 800]
            self.score += points[cleared] * self.level
            self.lines_cleared += cleared
            self.level = self.lines_cleared // 10 + 1

    
    def draw_line_clear_animation(self, lines_to_clear):
        for p in range(4):
            for y in lines_to_clear:
                pygame.draw.rect(
                    self.screen,
                    (0, 0, 0),
                    (0, y * BLOCK_SIZE, GRID_WIDTH * BLOCK_SIZE, BLOCK_SIZE)
                )
                for x in range(0, GRID_WIDTH):
                    if random.randint(0, 5) > 3:
                        self.draw_block(x, y, random.randint(1, 7))

            pygame.display.flip()
            pygame.time.delay(200 - (p * 50))


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

    def draw_block(self, x, y, color_idx, offset_x=0):
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

    def draw(self):
        self.screen.fill((20, 20, 20))
        
        # Spielfeld-Rahmen
        pygame.draw.rect(self.screen, (50, 50, 50),
                        (0, 0, GRID_WIDTH * BLOCK_SIZE, GRID_HEIGHT * BLOCK_SIZE), 2)
        
        # Grid zeichnen
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                self.draw_block(x, y, self.grid[y][x])
        
        # Aktuelles Stück zeichnen
        shape = self.current_piece['shape']
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    self.draw_block(
                        self.current_piece['x'] + x,
                        self.current_piece['y'] + y,
                        cell
                    )
        
        # Seitenleiste
        sidebar_x = GRID_WIDTH * BLOCK_SIZE + 10
        
        # Score
        score_text = self.font.render(f"Score: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (sidebar_x, 20))
        
        # Level
        level_text = self.font.render(f"Level: {self.level}", True, (255, 255, 255))
        self.screen.blit(level_text, (sidebar_x, 50))
        
        # Lines
        lines_text = self.font.render(f"Lines: {self.lines_cleared}", True, (255, 255, 255))
        self.screen.blit(lines_text, (sidebar_x, 80))
        
        # Nächstes Stück
        next_text = self.font.render("Next:", True, (255, 255, 255))
        self.screen.blit(next_text, (sidebar_x, 130))
        
        for y, row in enumerate(self.next_piece['shape']):
            for x, cell in enumerate(row):
                if cell:
                    self.draw_block(GRID_WIDTH + 1 + x, 6 + y, cell)
        
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
            
            if not self.game_over:
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
