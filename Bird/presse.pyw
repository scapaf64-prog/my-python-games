from ursina import *
import random

app = Ursina()

window.fps_counter.enabled = False

Sky()

camera.orthographic = True
camera.fov = 20
camera.background_color = color.rgb(164,183,198)


# -------------------------
# SOUNDS
# -------------------------

press_click = Audio('audio/press_click', autoplay=False, volume=1)
press_smash = Audio('audio/press_smash', autoplay=False, volume=1)
press_spring = Audio('audio/press_spring', autoplay=False, volume=1)


# -------------------------
# VOGEL
# -------------------------

bird = None

def create_bird():

    global bird

    bird = Animation('img/bird', fps=12, scale=2, x=0, y=0, filtering=False)

create_bird()


# -------------------------
# PRESSE
# -------------------------

top_pipe = Entity(model='quad', texture='white_cube', color=color.green, scale=(3,15,1), x=0, y=9)

bottom_pipe = Entity(model='quad', texture='white_cube', color=color.green, scale=(3,15,1), x=0, y=-9)

top_original_y = top_pipe.y
bottom_original_y = bottom_pipe.y


# -------------------------
# FEDERN
# -------------------------

def create_feathers():

    for i in range(4):

        feather = Entity(model='quad', texture='img/feather', scale=0.5, x=0, y=0, filtering=False)

        feather.animate_x(random.uniform(-3,3), duration=0.5)

        feather.animate_y(random.uniform(-1,3), duration=0.5)

        feather.animate_rotation_z(random.randint(-180,180), duration=0.5)

        feather.fade_out(duration=0.6)

        destroy(feather, delay=0.8)


# -------------------------
# PRESSE
# -------------------------

def activate_press():

    press_click.play()

    top_pipe.animate_y(top_original_y + 0.25, duration=0.06, curve=curve.out_quad)

    bottom_pipe.animate_y(bottom_original_y - 0.25, duration=0.06, curve=curve.out_quad)

    invoke(close_press, delay=0.15)

def close_press():

    global bird

    press_smash.play()

    # Vogel verschwindet

    if bird:
        bird.pause()
        destroy(bird)
        bird = None

    create_feathers()

    top_pipe.animate_y(2.7, duration=0.045, curve=curve.in_quad)

    bottom_pipe.animate_y(-2.7, duration=0.045, curve=curve.in_quad)

    invoke(reset_press, delay=0.25)

def reset_press():

    press_spring.play()

    top_pipe.animate_y(top_original_y, duration=0.35, curve=curve.out_elastic)

    bottom_pipe.animate_y(bottom_original_y, duration=0.35, curve=curve.out_elastic)


# -------------------------
# INPUT
# -------------------------

def input(key):

    if key == 'p':
        activate_press()

    if key == 'r':
        create_bird()

    if key == 'escape':
        application.quit()

app.run()

