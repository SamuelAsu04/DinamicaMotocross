import math
import sys
import pygame # type: ignore
import pymunk # type: ignore
import propiedades_moto as pm

from camara import Camera
from moto import Moto
from dibujado import draw_moto
from terreno import propiedades_segmentos, Terrain, SUELO_y
from colisiones_handler import registrar_handlers, estado_juego
from aerodinamica import Aerodinamica
from confi import WIDTH, HEIGHT,FPS

AERO        = 0.01        # escala m/px para el drag
tiempo_volcada = 0.0
def main():

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    try:
        fondo_img = pygame.image.load("motocross/fondo.png").convert()
        fondo_img = pygame.transform.smoothscale(fondo_img, (WIDTH, HEIGHT))
    except (pygame.error, FileNotFoundError):
        fondo_img = None  
    pygame.display.set_caption("Motocross 2D - Proyecto Final")
    clock = pygame.time.Clock()
    font  = pygame.font.SysFont(None, 22)

    space = pymunk.Space()
    space.gravity = (0, -900)

    # Manejadores
    registrar_handlers(
        space,
        cuerpos_ct=  pm.moto_propiedades,
        terrenos_ct = propiedades_segmentos
    )

    # Objetos Principales
    terrain     = Terrain(space)
    moto_objeto = Moto(space, position=(200, SUELO_y + 200))
    camara      = Camera()
    aero = Aerodinamica()

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
                    mx = moto_objeto.body.position.x
                    moto_objeto.reset((mx, terrain.altura_en(mx) + 200))

        
        moto = moto_objeto.body
        rueda_trasera = moto_objeto.ruedas[0]['body']

        # Controles
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHT]:
            acelerador = 1.0
        elif keys[pygame.K_LEFT]:
            acelerador = -0.4
        else:
            acelerador = 0.0

        inclinacion_back  = keys[pygame.K_UP]
        inclinacion_fwd   = keys[pygame.K_DOWN]
        inclinacion_state = 'back' if inclinacion_back else 'fwd' if inclinacion_fwd else 'neutral'

        aire = (estado_juego['contactos_activos'] == 0)

        sub_dt = dt / 4
        fx = fy = 0.0
        
        for _ in range(4):
            if aire:
                tau_chasis = 0.0
                if inclinacion_back:
                    tau_chasis = +pm.PILOT_TORQUE     
                elif inclinacion_fwd:
                    tau_chasis = -pm.PILOT_TORQUE 

                if tau_chasis != 0.0 and abs(moto.angular_velocity) < pm.OMEGA_MAX_AIRE:
                    moto.torque          += tau_chasis
                    rueda_trasera.torque += -tau_chasis
            else:
                patinando = moto_objeto.patina_trasera()
                moto_objeto.set_patinaje(patinando)

                T = acelerador * pm.PAR_MOTOR
                if patinando and acelerador > 0:
                    T *= pm.FACTOR_TRACCION
                rueda_trasera.torque += -T           


                if inclinacion_back:
                    moto.torque += pm.INCLINACION_TORQUE
                elif inclinacion_fwd:
                    moto.torque += -pm.INCLINACION_TORQUE

            v = moto_objeto.body.velocity
            fx, fy = aero.fuerza_drag((v.x * AERO, v.y * AERO), area=1, Cd=0.6)
            moto_objeto.body.apply_force_at_world_point((fx / AERO, fy / AERO), moto_objeto.body.position)

            space.step(sub_dt)

        moto_x, moto_y = moto.position

        ang = (moto.angle + math.pi) % (2 * math.pi) - math.pi  
        if (not aire) and abs(ang) > pm.VUELCO_ANGULO:
            tiempo_volcada += dt
            if tiempo_volcada > pm.VUELCO_TIEMPO:
                moto_objeto.reset((moto_x, terrain.altura_en(moto_x) + 200))
                tiempo_volcada = 0.0
        else:
            tiempo_volcada = 0.0

        # Actualizaciones
        camara.actu_camara(moto_x, moto_y)
        terrain.update(moto_x)

        if fondo_img:
            screen.blit(fondo_img, (0, 0))
        else:
            screen.fill((135, 206, 235))
        terrain.draw(screen, camara.x, camara.y)
        draw_moto(screen, moto_objeto, inclinacion_state, camara.x, camara.y)

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
            screen.blit(font.render(line, True, (255, 255, 255)), (10, 10 + i * 22))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()