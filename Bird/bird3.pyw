#
#  My Flappy Bird
#

from ursina import *
import random

app = Ursina()

window.fps_counter.enabled = False
window.entity_counter.enabled = False
window.collider_counter.enabled = False

Sky()

camera.orthographic = True
camera.fov = 20
camera.background_color = color.rgb(164,183,198)

bird = Animation(
    'img/bird',
    fps=12,
    scale=2,
    y=5,
    filtering=False
)

velocity = 0
gravity = -12
jump_force = 6
GROUND_Y = -9

wing_sound = Audio('audio/wing', autoplay=False, volume = 1.0 )
point_sound = Audio('audio/point', autoplay=False, volume = 1.0)
crash_sound = Audio('audio/crash', autoplay=False, volume = 1.0)
thud_sound = Audio('audio/thud', autoplay=False, volume = 1.0)

pipe_template = Entity(
    model='quad',
    texture='white_cube',
    color=color.green,
    scale=(3,15,1),
    collider='box',
    x=20
)

bird_hitbox = Entity(
    parent=bird,
    model='cube',
    scale=(0.2,0.2,1),
    collider='box',
    visible=False
)

pipes = []
pipe_timer = 0
pipe_interval = 2      # alle 2 Sekunden ein neues Rohrpaar
game_over = False
crashed = False
started = False
score = 0
game_over_text = None
score_text = None
restart_text = None
exit_text = None
lives = 3
life_birds = []
restart_pending = False
thud_played = False
waiting_restart = False

def start_game():
    global velocity, game_over, crashed, pipe_timer, started, waiting_restart, restart_pending, thud_played

    velocity = 0
    game_over = False
    crashed = False
    pipe_timer = 0
    started = False
    waiting_restart = False
    restart_pending = False
    thud_played = False

    bird.x = 0
    bird.y = 5
    bird.rotation_z = 0
    bird.resume()
    bird.start()

    update_lives()

def new_pipe():
    gap_y = random.randint(4,12)

    top = duplicate(pipe_template)
    top.x = 25
    top.y = gap_y

    bottom = duplicate(pipe_template)
    bottom.x = 25
    bottom.y = gap_y - 22

    # gemeinsamer Zähler für dieses Rohrpaar
    top.passed = False
    bottom.passed = True

    pipes.extend([top, bottom])


def update():
    global velocity, game_over, pipe_timer, score, game_over_text
    global crashed, thud_played, waiting_restart

    if waiting_restart:
        return

    if crashed:
        velocity -= 80 * time.dt
        bird.rotation_z = min(bird.rotation_z + 300 * time.dt, 70)

    if game_over:
        return

    if not started:
        return

    pipe_timer += time.dt

    if pipe_timer >= pipe_interval:
        pipe_timer = 0
        new_pipe()

    # normale Schwerkraft oder Absturz
    bird.y += velocity * time.dt

    if not crashed:
        velocity += gravity * time.dt

    if bird.y <= GROUND_Y:
        bird.y = GROUND_Y
        velocity = 0

        if crashed:
            bird.pause()

            if not thud_played:
                thud_sound.play()
                thud_played = True

            lose_life()

    # Rohre bewegen und löschen
    for p in pipes[:]:
        p.x -= 6 * time.dt

        if p.x < bird.x and not p.passed:
            score += 1
            p.passed = True
            point_sound.play()
            update_score()

        if p.x < -25:
            destroy(p)
            pipes.remove(p)

    # Kollision prüfen
    hit = bird_hitbox.intersects()

    if hit.hit and not crashed:
        crashed = True
        velocity = -5
        crash_sound.play()

    if bird.y > 12 and not crashed:
        crashed = True
        velocity = -5
        crash_sound.play()

def update_score():
    global score_text

    if score_text:
        destroy(score_text)

    score_text = Text(text=str(score), origin=(0,0), scale=5, y=0.4, color=color.light_gray, shadow=True)

def show_game_over():
    global game_over_text, restart_text, exit_text

    game_over_text = Text(
        text='GAME OVER',
        origin=(0,0),
        y=0,
        scale=3,
        color=color.red,
        shadow=True
    )

    restart_text = Text(
        text='Press R to Restart',
        origin=(0,0),
        y=-0.18,
        scale=1.2,
        color=color.light_gray
    )

    exit_text = Text(
        text='Press ESC to Quit',
        origin=(0,0),
        y=-0.28,
        scale=1.2,
        color=color.light_gray
    )

def update_lives():
    global life_birds

    # alte kleine Vögel entfernen
    for b in life_birds:
        destroy(b)

    life_birds.clear()

    # neue kleine Vögel oben rechts erzeugen
    for i in range(lives):
        b = Animation(
            'img/bird',
            fps=12,
            scale=0.5,
            x=-14 + i * 1,
            y=9,
            filtering=False
        )

        life_birds.append(b)
        b.pause()


def life_bird_hit_effect():
    if not life_birds:
        return

    b = life_birds[-1]

    b.color = color.light_gray

    # Geister-Effekt
    b.animate_scale(1.4, duration=0.18, curve=curve.out_back)
    b.animate_rotation_z(90, duration=0.35)
    b.animate_y(b.y + 0.5, duration=0.35)
    b.animate('alpha', 0, duration=0.35)

    invoke(make_life_bird_fade, b, delay=0.36)


def make_life_bird_fade(b):
    if b in life_birds:
        life_birds.remove(b)

    destroy(b)

def lose_life():
    global lives, crashed, game_over, restart_pending, waiting_restart

    if restart_pending:
        return

    restart_pending = True
    waiting_restart = True

    lives -= 1

    invoke(life_bird_hit_effect, delay=0.4)

    if lives <= 0:
        game_over = True
        show_game_over()
        return

    invoke(restart_after_crash, delay=1.0)

def restart_after_crash():
    global velocity, crashed, game_over, restart_pending, thud_played, waiting_restart, started

    for p in pipes:
        destroy(p)

    pipes.clear()

    velocity = 0

    bird.y = 5
    bird.rotation_z = 0
    bird.start()

    crashed = False
    game_over = False
    started = False

    restart_pending = False
    thud_played = False
    waiting_restart = False

def restart_game():
    global game_over_text, restart_text, exit_text
    global score, lives, pipe_timer

    if game_over_text:
        destroy(game_over_text)
        game_over_text = None

    if restart_text:
        destroy(restart_text)
        restart_text = None

    if exit_text:
        destroy(exit_text)
        exit_text = None

    for p in pipes:
        destroy(p)

    pipes.clear()

    pipe_timer = pipe_interval - 1

    score = 0
    update_score()

    lives = 3
    update_lives()

    start_game()

def input(key):
    global velocity, started

    if key == 'space' or key == 'up arrow':
        if not started:
            started = True

        if not game_over and not crashed:
            velocity = jump_force
            wing_sound.stop()
            wing_sound.play()

    elif key == 'r':
        restart_game()
    if key == 'escape':
        application.quit()

start_game()
update_lives()
pipe_timer = pipe_interval - 1
update_score()

app.run()


