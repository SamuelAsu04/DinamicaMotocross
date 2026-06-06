import math
import sys
import pygame
import pymunk
import moto as mt

# -----------------------------------------------------------------------------
# Configuración general
# -----------------------------------------------------------------------------
WIDTH, HEIGHT = 1200, 600
FPS = 60


# Controles (a tunear al gusto)
THROTTLE_RATE = -25          # si la moto va hacia atrás al acelerar, cambia el signo
BRAKE_RATE = 25
MOTOR_MAX_FORCE = 50_1000
LEAN_TORQUE = 80_000
# Mundo
GRAVITY = (0, -900)          # Y-up: gravedad hacia abajo (negativa)
GROUND_Y = 80                # altura del suelo (coords pymunk, desde abajo)


# -----------------------------------------------------------------------------
# Mundo
# -----------------------------------------------------------------------------
def make_ground(space):
    body = space.static_body
    shape = pymunk.Segment(body, (-2000, GROUND_Y), (4000, GROUND_Y), 5)
    shape.friction = 1.0
    shape.elasticity = 0.3
    space.add(shape)

# -----------------------------------------------------------------------------
# Render
# -----------------------------------------------------------------------------
def draw_ground(screen):
    pygame.draw.rect(
        screen, (110, 80, 50),
        pygame.Rect(0, HEIGHT - GROUND_Y, WIDTH, GROUND_Y),
    )

# -----------------------------------------------------------------------------
# Bucle principal
# -----------------------------------------------------------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Motocross 2D — esqueleto")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 20)

    assets = mt.load_assets()    # tras set_mode, para que convert_alpha() funcione

    space = pymunk.Space()
    space.gravity = GRAVITY

    make_ground(space)
    bike = mt.make_motorcycle(space, position=(200, GROUND_Y + 100))

    running = True
    while running:
        dt = 1.0 / FPS

        # ---------------- Eventos ----------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    mt.reset_bike(bike)

        # ---------------- Estado de teclas ----------------
        keys = pygame.key.get_pressed()
        motor = bike['motor']
        moto = bike['moto']

        if keys[pygame.K_LEFT]:
            motor.rate = THROTTLE_RATE
            motor.max_force = MOTOR_MAX_FORCE
        elif keys[pygame.K_RIGHT]:
            motor.rate = BRAKE_RATE
            motor.max_force = MOTOR_MAX_FORCE
        else:
            motor.rate = 0
            motor.max_force = 0

        lean_back = keys[pygame.K_UP]
        lean_fwd = keys[pygame.K_DOWN]
        if lean_back:
            lean_state = 'back'
        elif lean_fwd:
            lean_state = 'fwd'
        else:
            lean_state = 'neutral'

        # ---------------- Física (substepping) ----------------
        sub_steps = 4
        sub_dt = dt / sub_steps
        for _ in range(sub_steps):
            # body.torque se resetea en cada step => se reaplica dentro del bucle
            if lean_back:
                moto.torque = LEAN_TORQUE
            elif lean_fwd:
                moto.torque = -LEAN_TORQUE
            space.step(sub_dt)

        # ---------------- Render ----------------
        screen.fill((180, 210, 240))   # cielo
        draw_ground(screen)
        mt.draw_bike(screen, bike, assets, lean_state)

        hud = [
            f"v: {moto.velocity.length:6.1f} px/s   "
            f"ángulo: {math.degrees(moto.angle):6.1f}°   "
            f"ω: {moto.angular_velocity:5.2f} rad/s   "
            f"pose: {lean_state}",
        ]
        for i, line in enumerate(hud):
            screen.blit(font.render(line, True, (20, 20, 20)), (10, 10 + i * 20))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()