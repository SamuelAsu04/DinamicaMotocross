import math
import sys
import pygame
import pymunk

from moto import load_assets, crear_moto, reset_bike, draw_bike, WIDTH, HEIGHT, FPS
from terreno import Terrain, SUELO_y

GRAVEDAD         = (0, -900)
MOTOR_MAX_FORCE = 80_000
LEAN_TORQUE     = 80_000
CAMERA_OFFSET_X = WIDTH // 3
CAMERA_OFFSET_Y = HEIGHT // 3

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Motocross 2D")
    clock = pygame.time.Clock()
    font  = pygame.font.SysFont(None, 22)

    space = pymunk.Space()
    space.gravity = GRAVEDAD

    terrain  = Terrain(space)
    moto_objeto = crear_moto(space, position=(200, SUELO_y + 120))
    camera_x = 0.0
    camera_y = 0.0
    
    running = True
    while running:
        dt = 1.0 / FPS

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    reset_bike(moto_objeto)

        keys  = pygame.key.get_pressed()
        motor = moto_objeto['motor']
        moto  = moto_objeto['moto']

        if keys[pygame.K_LEFT]:
            motor.rate = -50
            motor.max_force = MOTOR_MAX_FORCE
        elif keys[pygame.K_RIGHT]:
            motor.rate = 50
            motor.max_force = MOTOR_MAX_FORCE
        else:
            motor.rate = 0
            motor.max_force = 0

        lean_back = keys[pygame.K_UP]
        lean_fwd  = keys[pygame.K_DOWN]
        lean_state = 'back' if lean_back else 'fwd' if lean_fwd else 'neutral'

        sub_dt = dt / 4
        for _ in range(4):
            if lean_back:
                moto.torque = LEAN_TORQUE
            elif lean_fwd:
                moto.torque = -LEAN_TORQUE
            space.step(sub_dt)

        moto_x    = moto.position.x
        moto_y    = moto.position.y
        camera_x += (moto_x - CAMERA_OFFSET_X - camera_x) * 0.12
        camera_y += (moto_y - CAMERA_OFFSET_Y - camera_y) * 0.12

        terrain.update(moto_x)

        screen.fill((180, 210, 240))
        terrain.draw(screen, camera_x, camera_y)
        draw_bike(screen, moto_objeto,lean_state, camera_x)

        hud = [
            f"v: {moto.velocity.length:6.1f} px/s   ángulo: {math.degrees(moto.angle):5.1f}°   distancia: {int(moto_x)} px",
            "← acelerar   → frenar   ↑ inclinarse atrás   ↓ inclinarse adelante   R reiniciar",
        ]
        for i, line in enumerate(hud):
            screen.blit(font.render(line, True, (20, 20, 20)), (10, 10 + i * 22))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()