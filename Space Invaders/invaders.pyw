#
#    Space Invaders
#

import pygame
import random
import os

# --- Globale Konstanten ---
WIDTH, HEIGHT = 1280, 720
WHITE = (255, 255, 255)
RED = (255, 60, 60)
BLUE = (50, 150, 255)
YELLOW = (255, 255, 0)

BASE = os.path.dirname(os.path.abspath(__file__))

# --- Spiele-Klassen ---

class SoundManager:
    def __init__(self):
        self.sounds = {}
        files = {
            "shoot": "shoot.wav",
            "hit": "schnapp.mp3",
            "gameover": "whoosh.mp3",
            "exp1": "explosion1.mp3",
            "exp2": "explosion.mp3",
            "exp3": "bubble1.mp3"
        }
        for k, f in files.items():
            try:
                self.sounds[k] = pygame.mixer.Sound(os.path.join(BASE, f))
                if k == "shoot":
                    self.sounds[k].set_volume(0.3)
            except:
                self.sounds[k] = None

    def play(self, name):
        s = self.sounds.get(name)
        if s:
            s.play()

    def explosion(self):
        ex = [self.sounds["exp1"], self.sounds["exp2"], self.sounds["exp3"]]
        ex = [x for x in ex if x]
        if ex:
            random.choice(ex).play()


class StarField:
    def __init__(self):
        self.stars = [[random.randint(0, WIDTH), random.randint(0, HEIGHT), random.randint(1, 3)] for _ in range(250)]

    def update(self):
        for s in self.stars:
            s[1] += s[2]
            if s[1] > HEIGHT:
                s[0] = random.randint(0, WIDTH)
                s[1] = 0

    def draw(self, screen):
        for s in self.stars:
            pygame.draw.circle(screen, WHITE, (s[0], s[1]), s[2])


class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.dx = random.uniform(-4, 4)
        self.dy = random.uniform(-4, 4)
        self.life = 30

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.life -= 1

    def draw(self, screen):
        if self.life > 0:
            pygame.draw.circle(screen, (255, 150, 0), (int(self.x), int(self.y)), 3)


class Projectile:
    def __init__(self, x, y, speed, color, w, h):
        self.x = x
        self.y = y
        self.speed = speed
        self.color = color
        self.w = w
        self.h = h

    def update(self):
        self.y += self.speed

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.x - self.w // 2, self.y, self.w, self.h))


class Bullet(Projectile):
    def __init__(self, x, y):
        super().__init__(x, y, -12, YELLOW, 4, 15)


class EnemyBullet(Projectile):
    def __init__(self, x, y):
        super().__init__(x, y, 5, RED, 6, 15)


class Player:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT - 100
        self.invincible = 0

    def move(self, keys):
        if keys[pygame.K_LEFT]: self.x -= 8
        if keys[pygame.K_RIGHT]: self.x += 8
        if keys[pygame.K_UP]: self.y -= 6
        if keys[pygame.K_DOWN]: self.y += 6
        self.x = max(25, min(WIDTH - 25, self.x))
        self.y = max(50, min(HEIGHT - 50, self.y))

    def draw(self, screen, dead=False, explosion=False):
        color = RED if dead else BLUE
        if not explosion:
            pygame.draw.polygon(screen, color, [(self.x, self.y - 30), (self.x - 25, self.y + 20), (self.x + 25, self.y + 20)])

    @property
    def rect(self):
        return pygame.Rect(self.x - 25, self.y - 30, 50, 50)


class Enemy:
    def __init__(self):
        self.x = random.randint(50, WIDTH - 90)
        self.y = random.randint(-300, -50)
        self.speed = random.uniform(2, 4)
        self.hp = random.randint(1, 3)

    def update(self):
        self.y += self.speed

    def draw(self, screen):
        color = (255, max(0, min(255, 50 * self.hp)), 50)
        pygame.draw.rect(screen, color, (self.x, self.y, 40, 40))
        pygame.draw.rect(screen, WHITE, (self.x, self.y, 40, 40), 2)

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, 40, 40)


class EnemySpawner:
    def spawn(self, score, enemies):
        rate = min(0.03, 0.01 + score * 0.00003)
        if len(enemies) < 30 and random.random() < rate:
            enemies.append(Enemy())


class HUD:
    def __init__(self):
        self.font = pygame.font.SysFont("Arial", 32)

    def draw(self, screen, score, lives):
        screen.blit(self.font.render(f"Score : {score}", True, WHITE), (20, 20))
        if lives < 2 and (pygame.time.get_ticks() // 500) % 2 == 0:
            txt = self.font.render(f"Shield: {lives}", True, RED)
        else:
            txt = self.font.render(f"Shield: {lives}", True, WHITE)
        screen.blit(txt, (20, 60))


# --- Haupt-Game-Klasse ---

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Space Invaders OOP")
        self.clock = pygame.time.Clock()
        self.sound = SoundManager()
        self.hud = HUD()
        self.starfield = StarField()
        self.spawner = EnemySpawner()
        self.reset()

    def reset(self):
        self.score = 0
        self.lives = 5
        self.kills_for_life = 0
        self.player = Player()
        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.particles = []
        self.player_dead = False
        self.death_timer = 0
        self.explosion_triggered = False

    def run(self):
        running = True
        while running:
            self.clock.tick(60)
            for e in pygame.event.get():
                if e.type == pygame.QUIT: 
                    running = False
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE: 
                        running = False
                    if e.key == pygame.K_SPACE and not self.player_dead:
                        self.bullets.append(Bullet(self.player.x, self.player.y))
                        self.sound.play("shoot")

            keys = pygame.key.get_pressed()
            if not self.player_dead:
                self.player.move(keys)

            if self.player.invincible > 0:
                self.player.invincible -= 1

            self.starfield.update()
            self.spawner.spawn(self.score, self.enemies)

            for b in self.bullets[:]:
                b.update()
                if b.y < 0: 
                    self.bullets.remove(b)

            for e in self.enemies[:]:
                e.update()
                if e.y > HEIGHT:
                    self.enemies.remove(e)
                    continue
                
                # Kollision: Spieler-Projektil trifft Gegner
                for b in self.bullets[:]:
                    if e.rect.colliderect(pygame.Rect(b.x - 2, b.y, 4, 15)):
                        e.hp -= 1
                        if b in self.bullets: 
                            self.bullets.remove(b)
                        if e.hp <= 0:
                            self.score += 10
                            self.kills_for_life += 1
                            if self.kills_for_life >= 3:
                                self.lives += 1
                                self.kills_for_life = 0
                            self.sound.explosion()
                            for _ in range(25):
                                self.particles.append(Particle(e.x + 20, e.y + 20))
                            if e in self.enemies:
                                self.enemies.remove(e)
                        break

                # OPTIMIERUNG: Kollision: Gegner rammt Spieler direkt
                if not self.player_dead and self.player.invincible == 0 and e.rect.colliderect(self.player.rect):
                    self.lives -= 1
                    self.player.invincible = 120
                    self.sound.play("hit")
                    if e in self.enemies:
                        self.enemies.remove(e)
                    if self.lives < 1:
                        self.player_dead = True
                        self.death_timer = 90

            # Gegnerisches Schießen organisieren
            cols = {}
            for e in self.enemies:
                c = e.x // 40
                if c not in cols or e.y > cols[c].y:
                    cols[c] = e
            for e in cols.values():
                if random.random() < 0.004:
                    self.enemy_bullets.append(EnemyBullet(e.x + 20, e.y + 40))

            # Kollision: Gegner-Projektil trifft Spieler
            for b in self.enemy_bullets[:]:
                b.update()
                if b.y > HEIGHT:
                    self.enemy_bullets.remove(b)
                    continue
                if self.player.invincible == 0 and self.player.rect.colliderect(pygame.Rect(b.x - 3, b.y, 6, 15)):
                    self.lives -= 1
                    self.player.invincible = 120
                    self.sound.play("hit")
                    if b in self.enemy_bullets:
                        self.enemy_bullets.remove(b)
                    if self.lives < 1 and not self.player_dead:
                        self.player_dead = True
                        self.death_timer = 90

            if self.player_dead:
                self.death_timer -= 1
                if self.death_timer <= 30 and not self.explosion_triggered:
                    self.explosion_triggered = True
                    self.sound.play("gameover")
                    for _ in range(50):
                        self.particles.append(Particle(self.player.x, self.player.y))
                if self.death_timer <= 0:
                    self.reset()

            for p in self.particles[:]:
                p.update()
            self.particles = [p for p in self.particles if p.life > 0]

            # --- Zeichnen ---
            self.screen.fill((5, 5, 25))
            self.starfield.draw(self.screen)

            draw_player = True
            if self.player_dead:
                draw_player = (self.death_timer // 3) % 2 == 0
            elif self.player.invincible > 0:
                draw_player = (self.player.invincible // 5) % 2 == 0

            if draw_player:
                self.player.draw(self.screen, self.player_dead, self.explosion_triggered)

            for obj in self.bullets + self.enemy_bullets: 
                obj.draw(self.screen)
            for e in self.enemies: 
                e.draw(self.screen)
            for p in self.particles: 
                p.draw(self.screen)

            self.hud.draw(self.screen, self.score, self.lives)
            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    Game().run()



