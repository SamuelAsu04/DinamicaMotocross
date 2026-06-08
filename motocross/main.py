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

GRAVEDAD    = (0, -900)
AERO        = 0.05          # escala m/px para el drag




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

        keys = pygame.key.get_pressed()
        moto = moto_objeto.body
        rueda_trasera = moto_objeto.ruedas[0]['body']

        # acelerador: RIGHT avanza, LEFT frena / marcha atras (mas suave)
        if keys[pygame.K_RIGHT]:
            throttle = 1.0
        elif keys[pygame.K_LEFT]:
            throttle = -0.4
        else:
            throttle = 0.0

        lean_back  = keys[pygame.K_UP]
        lean_fwd   = keys[pygame.K_DOWN]
        lean_state = 'back' if lean_back else 'fwd' if lean_fwd else 'neutral'

        aire = (estado_juego['contactos_activos'] == 0)

        sub_dt = dt / 4
        fx = fy = 0.0
        for _ in range(4):
            if aire:
                # --- Control de pitcheo por PAR INTERNO (chasis <-> rueda) ---
                # No hay par externo => L del sistema se CONSERVA. Sin autonivelado.
                # Tope de giro: si ya gira al maximo, dejamos de dar par (NO se reescribe omega).
                tau_chasis = 0.0
                if lean_back:
                    tau_chasis = +pm.PILOT_TORQUE      # morro arriba (backflip)
                elif lean_fwd:
                    tau_chasis = -pm.PILOT_TORQUE      # morro abajo

                if tau_chasis != 0.0 and abs(moto.angular_velocity) < pm.OMEGA_MAX_AIRE:
                    moto.torque          += tau_chasis
                    rueda_trasera.torque += -tau_chasis
            else:
                # --- Traccion por PAR en tierra ---
                # El patinaje EMERGE del cono de friccion de pymunk; aqui solo
                # cambiamos mu_s<->mu_k y recortamos el par si la rueda patina (control de traccion).
                vel_rueda      = abs(rueda_trasera.angular_velocity) * pm.rueda_RADIUS
                velocidad_moto = moto.velocity.length
                patinando      = (vel_rueda - velocidad_moto) > pm.SLIP_UMBRAL
                moto_objeto.set_patinaje(patinando)

                T = throttle * pm.PAR_MOTOR
                if patinando and throttle > 0:
                    T *= pm.FACTOR_TRACCION
                rueda_trasera.torque += -T             # -T => la rueda rueda hacia +x (avance)

                # cambio de peso al inclinar en tierra (opcional, como tenias)
                if lean_back:
                    moto.torque += pm.LEAN_TORQUE
                elif lean_fwd:
                    moto.torque += -pm.LEAN_TORQUE

            # --- Drag aerodinamico (siempre): limitador natural de la velocidad punta ---
            v = moto_objeto.body.velocity
            fx, fy = aero.fuerza_drag((v.x * AERO, v.y * AERO), area=1, Cd=0.6)
            moto_objeto.body.apply_force_at_local_point((fx / AERO, fy / AERO), (0, 0))

            space.step(sub_dt)

        moto_x, moto_y = moto.position

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
            f"Drag: {abs(fx / AERO):.0f}"
        ]
        for i, line in enumerate(hud):
            screen.blit(font.render(line, True, (20, 20, 20)), (10, 10 + i * 22))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()