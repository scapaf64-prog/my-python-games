
import pygame
import random
import os

pygame.init()

WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invaders")

clock = pygame.time.Clock()

WHITE = (255, 255, 255)
RED = (255, 60, 60)
BLUE = (50, 150, 255)
YELLOW = (255, 255, 0)

font = pygame.font.SysFont("Arial", 32)

# Sound

BASE = os.path.dirname(os.path.abspath(__file__))

try:
    shoot_sound = pygame.mixer.Sound(os.path.join(BASE, "shoot.wav"))
    shoot_sound.set_volume(0.3)
except:
    shoot_sound = None

try:
    explosion_sounds = [
        pygame.mixer.Sound(os.path.join(BASE, "explosion1.mp3")),
        pygame.mixer.Sound(os.path.join(BASE, "explosion.mp3")),
        pygame.mixer.Sound(os.path.join(BASE, "bubble1.mp3"))
    ]

    for sound in explosion_sounds:
        sound.set_volume(0.8)
except:
    explosion_sounds = []

try:
    treffer_sound = pygame.mixer.Sound(os.path.join(BASE, "schnapp.mp3"))
    treffer_sound.set_volume(0.5)
except:
    treffer_sound = None

try:
    ende_sound = pygame.mixer.Sound(os.path.join(BASE, "whoosh.mp3"))
    ende_sound.set_volume(0.8)
except:
    ende_sound = None

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

    def draw(self):
        pygame.draw.circle(screen, (255, 150, 0), (int(self.x), int(self.y)), 3)


class Bullet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 12

    def update(self):
        self.y -= self.speed

    def draw(self):
        pygame.draw.rect(screen, YELLOW, (self.x - 2, self.y, 4, 15))


class EnemyBullet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 5

    def update(self):
        self.y += self.speed

    def draw(self):
        pygame.draw.rect(screen, RED, (self.x - 3, self.y, 6, 15))


class Enemy:
    def __init__(self):
        self.x = random.randint(50, WIDTH - 90)
        self.y = random.randint(-300, -50)
        self.speed = random.uniform(2, 4)
        self.hp = random.randint(1, 3)

    def update(self):
        self.y += self.speed

    def draw(self):
        color = (255, 50 * self.hp, 50)
        pygame.draw.rect(screen, color, (self.x, self.y, 40, 40))
        pygame.draw.rect(screen, WHITE, (self.x, self.y, 40, 40), 2)


class Game:
    def __init__(self):
        self.running = True
        self.reset_game()

        self.stars = []
        for _ in range(250):
            self.stars.append([
                random.randint(0, WIDTH),
                random.randint(0, HEIGHT),
                random.randint(1, 3)
            ])

    def reset_game(self):
        self.score = 0
        self.lives = 5
        self.kills_for_life = 0

        self.player_x = WIDTH // 2
        self.player_y = HEIGHT - 100

        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.particles = []

        self.invincible = 0
        self.player_dead = False
        self.death_timer = 0
        self.explosion_triggered = False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

                if event.key == pygame.K_SPACE:
                    self.bullets.append(Bullet(self.player_x, self.player_y))

                    if shoot_sound:
                        shoot_sound.play()

    def update(self):

        keys = pygame.key.get_pressed()

        if not self.player_dead:

            if keys[pygame.K_LEFT]:
                self.player_x -= 8

            if keys[pygame.K_RIGHT]:
                self.player_x += 8

            self.player_x = max(25, min(WIDTH - 25, self.player_x))

            if keys[pygame.K_UP]:
                self.player_y -= 6

            if keys[pygame.K_DOWN]:
                self.player_y += 6

            self.player_y = max(50, min(HEIGHT - 50, self.player_y))

        if self.invincible > 0:
            self.invincible -= 1

        if self.player_dead:

            self.death_timer -= 1

            if self.death_timer <= 30 and not self.explosion_triggered:

                self.explosion_triggered = True

                if ende_sound:
                    ende_sound.play()

                for _ in range(50):
                    self.particles.append(
                        Particle(self.player_x, self.player_y)
                    )

            if self.death_timer <= 0:
                self.reset_game()

        spawn_rate = min(0.03, 0.01 + self.score * 0.00003)

        if len(self.enemies) < 30 and random.random() < spawn_rate:
            self.enemies.append(Enemy())

        for star in self.stars:
            star[1] += star[2]

            if star[1] > HEIGHT:
                star[0] = random.randint(0, WIDTH)
                star[1] = 0

        for bullet in self.bullets[:]:
            bullet.update()

            if bullet.y < 0:
                self.bullets.remove(bullet)

        for enemy in self.enemies[:]:
            enemy.update()

            if enemy.y > HEIGHT:
                self.enemies.remove(enemy)
                continue

            for bullet in self.bullets[:]:

                enemy_rect = pygame.Rect(enemy.x, enemy.y, 40, 40)
                bullet_rect = pygame.Rect(bullet.x - 2, bullet.y, 4, 15)

                if enemy_rect.colliderect(bullet_rect):

                    enemy.hp -= 1

                    if bullet in self.bullets:
                        self.bullets.remove(bullet)

                    if enemy.hp <= 0:

                        self.score += 10
                        self.kills_for_life += 1

                        if self.kills_for_life >= 3:
                            self.lives += 1
                            self.kills_for_life = 0

                        if explosion_sounds:
                            random.choice(explosion_sounds).play()

                        for _ in range(25):
                            self.particles.append(
                                Particle(enemy.x + 20, enemy.y + 20)
                            )

                        if enemy in self.enemies:
                            self.enemies.remove(enemy)

                    break

        columns = {}

        for enemy in self.enemies:
            col = enemy.x // 40

            if col not in columns:
                columns[col] = enemy
            elif enemy.y > columns[col].y:
                columns[col] = enemy

        shooters = list(columns.values())

        for enemy in shooters:

            if random.random() < 0.004:
                self.enemy_bullets.append(
                    EnemyBullet(enemy.x + 20, enemy.y + 40)
                )

        player_rect = pygame.Rect(
            self.player_x - 25,
            self.player_y - 30,
            50,
            50
        )

        for bullet in self.enemy_bullets[:]:

            bullet.update()

            if bullet.y > HEIGHT:
                self.enemy_bullets.remove(bullet)
                continue

            bullet_rect = pygame.Rect(
                bullet.x - 3,
                bullet.y,
                6,
                15
            )

            if self.invincible == 0 and player_rect.colliderect(bullet_rect):

                self.lives -= 1
                self.invincible = 120

                if treffer_sound:
                    treffer_sound.play()

                if self.lives < 1 and not self.player_dead:
                    self.player_dead = True
                    self.death_timer = 90

                if bullet in self.enemy_bullets:
                    self.enemy_bullets.remove(bullet)

        for particle in self.particles[:]:
            particle.update()

        self.particles = [p for p in self.particles if p.life > 0]

    def draw(self):

        screen.fill((5, 5, 25))

        for star in self.stars:
            pygame.draw.circle(screen, WHITE, (star[0], star[1]), star[2])

        draw_player = True
        color = BLUE

        if self.player_dead:
            draw_player = (self.death_timer // 3) % 2 == 0
            color = RED

        elif self.invincible > 0:
            draw_player = (self.invincible // 5) % 2 == 0

        if draw_player and not self.explosion_triggered:
            pygame.draw.polygon(
                screen,
                color,
                [
                    (self.player_x, self.player_y - 30),
                    (self.player_x - 25, self.player_y + 20),
                    (self.player_x + 25, self.player_y + 20)
                ]
            )

        for bullet in self.bullets:
            bullet.draw()

        for bullet in self.enemy_bullets:
            bullet.draw()

        for enemy in self.enemies:
            enemy.draw()

        for particle in self.particles:
            particle.draw()

        score_text = font.render(f"Score : {self.score}", True, WHITE)

        if self.lives < 2:
            if (pygame.time.get_ticks() // 500) % 2 == 0:
                lives_text = font.render(f"Shield: {self.lives}", True, RED)
            else:
                lives_text = font.render(" ", True, WHITE)
        else:
            lives_text = font.render(f"Shield: {self.lives}", True, WHITE)

        screen.blit(score_text, (20, 20))
        screen.blit(lives_text, (20, 60))

        pygame.display.flip()


game = Game()

while game.running:
    clock.tick(60)
    game.handle_events()
    game.update()
    game.draw()

pygame.quit()
