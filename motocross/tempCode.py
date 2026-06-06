import math
import sys
import pygame
import pymunk


# -----------------------------------------------------------------------------
#  RUTAS DE LOS ASSETS  --  Cambia aquí las rutas de tus imágenes
# -----------------------------------------------------------------------------
ASSET_PATHS = {
    'wheel':          'motocross/rueda.png',
    'bike_neutral':   'motocross/bike1.png',
    'bike_lean_back': 'motocross/bike3.png',
    'bike_lean_fwd':  'motocross/bike2.png',
}


# -----------------------------------------------------------------------------
# Configuración general
# -----------------------------------------------------------------------------
WIDTH, HEIGHT = 1200, 600
FPS = 60

# Mundo
GRAVITY = (0, -900)          # Y-up: gravedad hacia abajo (negativa)
GROUND_Y = 80                # altura del suelo (coords pymunk, desde abajo)

# Chasis (caja de colisión — el sprite puede ser más grande visualmente)
CHASSIS_SIZE = (80, 20)
CHASSIS_MASS = 4.0

# Ruedas
WHEEL_RADIUS = 16
WHEEL_MASS = 1.0
WHEEL_FRICTION = 1.5
WHEEL_ELASTICITY = 0.2

# Suspensión
WHEEL_OFFSET_X = 36
SUSPENSION_LENGTH = 24
SUSPENSION_STIFFNESS = 800
SUSPENSION_DAMPING = 30

# Controles (a tunear al gusto)
THROTTLE_RATE = -25          # si la moto va hacia atrás al acelerar, cambia el signo
BRAKE_RATE = 25
MOTOR_MAX_FORCE = 50_000
LEAN_TORQUE = 80_000

# Tamaño visual de los sprites (no afecta a la física, solo al render)
WHEEL_SPRITE_DIAMETER = 2 * WHEEL_RADIUS + 4    # un pelín mayor que la hitbox
BIKE_SPRITE_WIDTH = 110                     # ancho del sprite chasis+piloto


# -----------------------------------------------------------------------------
# Carga de imágenes
# -----------------------------------------------------------------------------
def _scale_to_width(surface, target_width):
    """Escala una surface a `target_width` manteniendo la proporción."""
    w, h = surface.get_size()
    if w == 0:
        return surface
    target_height = max(1, int(h * target_width / w))
    return pygame.transform.smoothscale(surface, (target_width, target_height))


def load_assets():
    """Carga las imágenes de ASSET_PATHS y las redimensiona.

    Las ruedas se escalan a WHEEL_SPRITE_DIAMETER y los tres sprites de
    la moto a BIKE_SPRITE_WIDTH (la altura se ajusta para mantener
    proporción). Si alguna ruta falla, guarda None y se usa un placeholder.
    Debe llamarse DESPUÉS de pygame.display.set_mode().
    """
    assets = {}
    for key, path in ASSET_PATHS.items():
        try:
            img = pygame.image.load(path).convert_alpha()
            target = WHEEL_SPRITE_DIAMETER if key == 'wheel' else BIKE_SPRITE_WIDTH
            assets[key] = _scale_to_width(img, target)
        except (pygame.error, FileNotFoundError) as e:
            print(f"[aviso] No se pudo cargar '{path}' ({e}). Uso placeholder.")
            assets[key] = None
    return assets


# -----------------------------------------------------------------------------
# Conversión de coordenadas (pymunk Y-up -> pygame Y-down)
# -----------------------------------------------------------------------------
def to_pygame(p):
    return int(p[0]), int(HEIGHT - p[1])


# -----------------------------------------------------------------------------
# Mundo
# -----------------------------------------------------------------------------
def make_ground(space):
    body = space.static_body
    shape = pymunk.Segment(body, (-2000, GROUND_Y), (4000, GROUND_Y), 5)
    shape.friction = 1.0
    shape.elasticity = 0.3
    space.add(shape)


def make_motorcycle(space, position):
    """Chasis + 2 ruedas + suspensiones + motor en la rueda trasera."""
    px, py = position

    # --- Chasis ---
    cw, ch = CHASSIS_SIZE
    chassis = pymunk.Body(CHASSIS_MASS, pymunk.moment_for_box(CHASSIS_MASS, (cw, ch)))
    chassis.position = px, py
    chassis_shape = pymunk.Poly.create_box(chassis, (cw, ch))
    chassis_shape.friction = 0.4
    chassis_shape.elasticity = 0.1
    chassis_shape.filter = pymunk.ShapeFilter(group=1)
    space.add(chassis, chassis_shape)

    # --- Ruedas + suspensión ---
    wheels = []
    for side, offset_x in [('rear', -WHEEL_OFFSET_X), ('front', WHEEL_OFFSET_X)]:
        wheel = pymunk.Body(
            WHEEL_MASS,
            pymunk.moment_for_circle(WHEEL_MASS, 0, WHEEL_RADIUS),
        )
        wheel.position = px + offset_x, py - SUSPENSION_LENGTH
        wheel_shape = pymunk.Circle(wheel, WHEEL_RADIUS)
        wheel_shape.friction = WHEEL_FRICTION
        wheel_shape.elasticity = WHEEL_ELASTICITY
        wheel_shape.filter = pymunk.ShapeFilter(group=1)
        space.add(wheel, wheel_shape)

        groove = pymunk.GrooveJoint(
            chassis, wheel,
            (offset_x, 10),
            (offset_x, -SUSPENSION_LENGTH - 10),
            (0, 0),
        )
        spring = pymunk.DampedSpring(
            chassis, wheel,
            (offset_x, 0), (0, 0),
            SUSPENSION_LENGTH, SUSPENSION_STIFFNESS, SUSPENSION_DAMPING,
        )
        space.add(groove, spring)

        wheels.append({'body': wheel, 'side': side, 'offset_x': offset_x})

    # --- Motor en la rueda trasera ---
    rear_wheel = wheels[0]['body']
    motor = pymunk.SimpleMotor(chassis, rear_wheel, 0)
    motor.max_force = 0
    space.add(motor)

    return {
        'chassis': chassis,
        'wheels': wheels,
        'motor': motor,
        'spawn': (px, py),
    }


def reset_bike(bike):
    px, py = bike['spawn']
    bike['chassis'].position = px, py
    bike['chassis'].velocity = (0, 0)
    bike['chassis'].angle = 0
    bike['chassis'].angular_velocity = 0
    for w in bike['wheels']:
        w['body'].position = px + w['offset_x'], py - SUSPENSION_LENGTH
        w['body'].velocity = (0, 0)
        w['body'].angle = 0
        w['body'].angular_velocity = 0


# -----------------------------------------------------------------------------
# Render
# -----------------------------------------------------------------------------
def draw_ground(screen):
    pygame.draw.rect(
        screen, (110, 80, 50),
        pygame.Rect(0, HEIGHT - GROUND_Y, WIDTH, GROUND_Y),
    )


def _blit_rotated(screen, image, center_pygame, angle_radians):
    """Rota la imagen según el ángulo físico y la pega centrada."""
    # pygame.transform.rotate gira CCW con ángulo positivo. Como pymunk usa
    # Y-up y pygame Y-down, el ángulo aplicado coincide en sentido visual
    # (al rodar hacia la derecha, body.angle decrece => giro horario en pantalla).
    rotated = pygame.transform.rotate(image, math.degrees(angle_radians))
    rect = rotated.get_rect(center=center_pygame)
    screen.blit(rotated, rect)


def _draw_chassis_placeholder(screen, chassis):
    cw, ch = CHASSIS_SIZE
    cos_a, sin_a = math.cos(chassis.angle), math.sin(chassis.angle)
    cx, cy = chassis.position
    corners_local = [(-cw / 2, -ch / 2), (cw / 2, -ch / 2),
                     (cw / 2, ch / 2), (-cw / 2, ch / 2)]
    corners = []
    for x, y in corners_local:
        wx = cx + x * cos_a - y * sin_a
        wy = cy + x * sin_a + y * cos_a
        corners.append(to_pygame((wx, wy)))
    pygame.draw.polygon(screen, (200, 40, 40), corners)
    pygame.draw.polygon(screen, (30, 0, 0), corners, 2)


def _draw_wheel_placeholder(screen, body):
    center = to_pygame(body.position)
    pygame.draw.circle(screen, (35, 35, 35), center, WHEEL_RADIUS)
    pygame.draw.circle(screen, (160, 160, 160), center, WHEEL_RADIUS, 2)
    ex = center[0] + int(WHEEL_RADIUS * math.cos(body.angle))
    ey = center[1] - int(WHEEL_RADIUS * math.sin(body.angle))
    pygame.draw.line(screen, (255, 230, 60), center, (ex, ey), 2)


def draw_bike(screen, bike, assets, lean_state):
    """Dibuja la moto usando imágenes (con fallback geométrico si faltan).

    lean_state: 'neutral' | 'back' | 'fwd'  -> elige el sprite del chasis.
    """

    wheel_img = assets.get('wheel')
    for w in bike['wheels']:
        body = w['body']
        if wheel_img is not None:
            _blit_rotated(screen, wheel_img, to_pygame(body.position), body.angle)
        else:
            _draw_wheel_placeholder(screen, body)

    chassis = bike['chassis']
    bike_key = {
        'back':    'bike_lean_back',
        'fwd':     'bike_lean_fwd',
        'neutral': 'bike_neutral',
    }[lean_state]
    chassis_img = assets.get(bike_key)
    if chassis_img is not None:
        _blit_rotated(screen, chassis_img, to_pygame(chassis.position), chassis.angle)
    else:
        _draw_chassis_placeholder(screen, chassis)




# -----------------------------------------------------------------------------
# Bucle principal
# -----------------------------------------------------------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Motocross 2D — esqueleto")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 20)

    assets = load_assets()    # tras set_mode, para que convert_alpha() funcione

    space = pymunk.Space()
    space.gravity = GRAVITY

    make_ground(space)
    bike = make_motorcycle(space, position=(200, GROUND_Y + 100))

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
                    reset_bike(bike)

        # ---------------- Estado de teclas ----------------
        keys = pygame.key.get_pressed()
        motor = bike['motor']
        chassis = bike['chassis']

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
                chassis.torque = LEAN_TORQUE
            elif lean_fwd:
                chassis.torque = -LEAN_TORQUE
            space.step(sub_dt)

        # ---------------- Render ----------------
        screen.fill((180, 210, 240))   # cielo
        draw_ground(screen)
        draw_bike(screen, bike, assets, lean_state)

        hud = [
            f"v: {chassis.velocity.length:6.1f} px/s   "
            f"ángulo: {math.degrees(chassis.angle):6.1f}°   "
            f"ω: {chassis.angular_velocity:5.2f} rad/s   "
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