import math
import pygame
import pymunk
import pymunk.pygame_util

# ----------------------------
# CONFIG
# ----------------------------
WIDTH, HEIGHT = 1000, 700
FPS = 60

R1 = 30
R2 = 120

CENTER1 = (350, 350)
CENTER2 = (350 + R1 + R2, 350)

# ----------------------------
# INIT
# ----------------------------
pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Demostración de engranajes (Gear Constraint)")

clock = pygame.time.Clock()

font = pygame.font.SysFont("consolas", 24)

space = pymunk.Space()
space.gravity = (0, 0)

draw_options = pymunk.pygame_util.DrawOptions(screen)

# ----------------------------
# CREATE BODIES
# ----------------------------

def create_wheel(pos, radius, mass=5):

    moment = pymunk.moment_for_circle(mass, 0, radius)

    body = pymunk.Body(mass, moment)
    body.position = pos

    shape = pymunk.Circle(body, radius)
    shape.friction = 1.0
    shape.color = (200, 200, 200, 255)

    space.add(body, shape)

    return body, shape


wheel1, shape1 = create_wheel(CENTER1, R1)
wheel2, shape2 = create_wheel(CENTER2, R2)

# ----------------------------
# FIX WHEELS IN PLACE
# ----------------------------

pivot1 = pymunk.PivotJoint(
    space.static_body,
    wheel1,
    CENTER1
)

pivot2 = pymunk.PivotJoint(
    space.static_body,
    wheel2,
    CENTER2
)

space.add(pivot1, pivot2)

# ----------------------------
# GEAR CONSTRAINT
# ----------------------------

gear = pymunk.GearJoint(
    wheel1,
    wheel2,
    phase=0,
    ratio=-(R2 / R1)
)

space.add(gear)

# ----------------------------
# MOTOR
# ----------------------------

motor = pymunk.SimpleMotor(
    space.static_body,
    wheel1,
    6.0
)

motor.max_force = 1_000_000

space.add(motor)

# ----------------------------
# DRAW ROTATION LINES
# ----------------------------

def draw_rotation_line(body, radius, color):

    x, y = body.position
    angle = body.angle

    end_x = x + math.cos(angle) * radius
    end_y = y + math.sin(angle) * radius

    pygame.draw.line(
        screen,
        color,
        (x, y),
        (end_x, end_y),
        4
    )

# ----------------------------
# TEXT
# ----------------------------

def draw_text(text, pos, color=(255, 255, 255)):
    surface = font.render(text, True, color)
    screen.blit(surface, pos)

# ----------------------------
# MAIN LOOP
# ----------------------------

running = True

while running:

    dt = 1 / FPS

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    space.step(dt)

    screen.fill((30, 30, 30))

    # debug draw
    space.debug_draw(draw_options)

    # líneas de giro
    draw_rotation_line(wheel1, R1, (255, 0, 0))
    draw_rotation_line(wheel2, R2, (0, 255, 0))

    # ----------------------------
    # ANGULAR VELOCITIES
    # ----------------------------

    w1 = wheel1.angular_velocity
    w2 = wheel2.angular_velocity

    draw_text(f"Rueda 1 ω = {w1:.2f} rad/s", (40, 40))
    draw_text(f"Rueda 2 ω = {w2:.2f} rad/s", (40, 80))

    # ratio teórico
    if abs(w2) > 0.0001:
        ratio = w1 / w2
        draw_text(f"ω1 / ω2 = {ratio:.2f}", (40, 120))

    pygame.display.flip()

    clock.tick(FPS)

pygame.quit()
