import math
import sys
import pygame # type: ignore
import pymunk # type: ignore
import propiedades_moto as pm

from camara import Camera
from moto import Moto
from dibujado import draw_bike
from terreno import propiedades_segmentos, Terrain, SUELO_y
from colisiones_handler import registrar_handlers, estado_juego
from aerodinamica import Aerodinamica


aero = Aerodinamica()

WIDTH, HEIGHT = 1200, 600
FPS = 60

GRAVEDAD        = (0, -900)
MOTOR_MAX_FORCE = 2_000_000
LEAN_TORQUE     = 500_000

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Motocross 2D")
    clock = pygame.time.Clock()
    font  = pygame.font.SysFont(None, 22)
    
    space = pymunk.Space()
    space.gravity = GRAVEDAD

    registrar_handlers(
        space,
        ruedas_ct   = pm.ruedas_propiedades,
        terrenos_ct = propiedades_segmentos
    )

    terrain     = Terrain(space)
    moto_objeto = Moto(space, position=(200, SUELO_y + 200))
    camara = Camera()
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
                    moto_objeto.reset()

        keys  = pygame.key.get_pressed()
        motor = moto_objeto.motor
        moto  = moto_objeto.body

        if keys[pygame.K_LEFT]:
            motor.rate = -50
            motor.max_force = MOTOR_MAX_FORCE
        elif keys[pygame.K_RIGHT]:
            motor.rate = 200
            motor.max_force = MOTOR_MAX_FORCE
        else:
            motor.rate = 0
            motor.max_force = 0

        lean_back  = keys[pygame.K_UP]
        lean_fwd   = keys[pygame.K_DOWN]
        lean_state = 'back' if lean_back else 'fwd' if lean_fwd else 'neutral'

        aire = (estado_juego['contactos_activos'] == 0)
        
        sub_dt = dt / 4
        for _ in range(4):
            if aire: 
                motor.max_force = 0 
                if lean_back:
                    moto.torque = pm.TORQUE_AIRE
                elif lean_fwd:
                    moto.torque = -pm.TORQUE_AIRE
                else:
                  
                    moto.torque = -pm.ESTABILIZACION * moto.angular_velocity

                moto.angular_velocity = max(-pm.OMEGA_MAX_AIRE, min(pm.OMEGA_MAX_AIRE, moto.angular_velocity))
            else:
                if lean_back:
                    moto.torque = LEAN_TORQUE
                elif lean_fwd:
                    moto.torque = -LEAN_TORQUE
           
            v = moto_objeto.body.velocity
            v_ms = (v.x * 0.1, v.y * 0.1)  

            fx, fy = aero.fuerza_drag(v_ms, area=1, Cd=0.6)

            # reescalar la fuerza de vuelta a unidades del juego
            moto_objeto.body.apply_force_at_local_point(
                (fx / 0.1, fy / 0.1), (0, 0)
            )

            rueda_trasera = moto_objeto.ruedas[0]['body']
            velocidad_moto = moto_objeto.body.velocity.length

            # la rueda patiná si gira mucho más rápido que la velocidad del vehículo
            vel_rueda = abs(rueda_trasera.angular_velocity) * pm.rueda_RADIUS
            patinando = (vel_rueda > velocidad_moto + pm.MOTOR_RATE_PATINAJE) and not aire

            moto_objeto.set_patinaje(patinando)
            space.step(sub_dt)

        
    
        moto_x,  moto_y = moto.position
        
        camara.actu_camara(moto_x, moto_y)
        terrain.update(moto_x)

        screen.fill((180, 210, 240))
        terrain.draw(screen, camara.x, camara.y)
        draw_bike(screen, moto_objeto, lean_state, camara.x, camara.y)

        L = moto_objeto.momento_angular()
        
        hud = [
            f"Velocidad: {moto.velocity.length:6.1f} px/s   "
            f"Angulo: {math.degrees(moto.angle):5.1f}°   "
            f"Distancia: {int(moto_x)} px",
            f"Impulso aterrizaje: {estado_juego['ultimo_impulso']:.0f}   "
            f"L = {L:.1f} kg·px²/s   ω = {moto.angular_velocity:.2f} rad/s   {'EN AIRE' if aire else 'en suelo'}",
            f"Drag: {abs(fx/0.1):.0f}"
        ]
        for i, line in enumerate(hud):
            screen.blit(font.render(line, True, (20, 20, 20)), (10, 10 + i * 22))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()