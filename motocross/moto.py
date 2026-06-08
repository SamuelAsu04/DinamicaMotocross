import math
import pygame
import pymunk
import propiedades_moto as pm

WIDTH, HEIGHT = 1200, 600
FPS = 60

ASSET_PATHS = {
    'rueda':          'motocross/rueda.png',
    'bike_neutral':   'motocross/bike1.png',
    'bike_lean_back': 'motocross/bike3.png',
    'bike_lean_fwd':  'motocross/bike2.png',
}


def scale_to_width(surface, target_width):
    w, h = surface.get_size()
    if w == 0:
        return surface
    target_height = max(1, int(h * target_width / w))
    return pygame.transform.smoothscale(surface, (target_width, target_height))


def load_assets():
    assets = {}
    for key, path in ASSET_PATHS.items():
        try:
            img = pygame.image.load(path).convert_alpha()
            target = pm.rueda_SPRITE_DIAMETER if key == 'rueda' else pm.BIKE_SPRITE_WIDTH
            assets[key] = scale_to_width(img, target)
        except (pygame.error, FileNotFoundError) as e:
            print(f"[aviso] No se pudo cargar '{path}' ({e}). Uso placeholder.")
            assets[key] = None
    return assets

def to_pygame(p, camera_x=0, camera_y=0):
    return int(p[0] - camera_x), int(HEIGHT - p[1] + camera_y)

def crear_moto(space, position):
    px, py = position

    cw, ch = pm.moto_SIZE
    moto = pymunk.Body(pm.moto_MASS, pymunk.moment_for_box(pm.moto_MASS, (cw, ch)))
    moto.position = px, py
    moto_shape = pymunk.Poly.create_box(moto, (cw, ch))
    moto_shape.friction = 0.4
    moto_shape.elasticity = 0.1
    moto_shape.filter = pymunk.ShapeFilter(group=1)
    space.add(moto, moto_shape)

    ruedas = []
    for side, offset_x in [(1, -pm.rueda_OFFSET_X), (2, pm.rueda_OFFSET_X)]:
        rueda = pymunk.Body(pm.rueda_MASS, pymunk.moment_for_circle(pm.rueda_MASS, 0, pm.rueda_RADIUS))
        rueda.position = px + offset_x, py - pm.SUSPENSION_LENGTH
        rueda_shape = pymunk.Circle(rueda, pm.rueda_RADIUS)
        rueda_shape.friction = pm.rueda_FRICTION
        rueda_shape.elasticity = pm.rueda_ELASTICITY
        rueda_shape.collision_type = side
        rueda_shape.filter = pymunk.ShapeFilter(group=1)
        space.add(rueda, rueda_shape)

        groove = pymunk.GrooveJoint(
            moto, rueda,
            (offset_x, 10), (offset_x, -pm.SUSPENSION_LENGTH - 10), (0, 0),
        )
        spring = pymunk.DampedSpring(
            moto, rueda, (offset_x, 0), (0, 0),
            pm.SUSPENSION_LENGTH, pm.SUSPENSION_STIFFNESS, pm.SUSPENSION_DAMPING,
        )
        space.add(groove, spring)
        ruedas.append({'body': rueda, 'side': side, 'offset_x': offset_x})

    rear_rueda = ruedas[0]['body']
    motor = pymunk.SimpleMotor(moto, rear_rueda, 0)
    motor.max_force = 0
    space.add(motor)

    return {'moto': moto, 'ruedas': ruedas, 'motor': motor, 'spawn': (px, py), 'aire': False,'colisiones_ruedas': 0}

def reset_bike(bike):
    px, py = bike['spawn']
    bike['moto'].position = px, py
    bike['moto'].velocity = (0, 0)
    bike['moto'].angle = 0
    bike['moto'].angular_velocity = 0
    for w in bike['ruedas']:
        w['body'].position = px + w['offset_x'], py - pm.SUSPENSION_LENGTH
        w['body'].velocity = (0, 0)
        w['body'].angle = 0
        w['body'].angular_velocity = 0

# -----------------------------------------------------------------------------
# Dibujar
# -----------------------------------------------------------------------------
def blit_rotated(screen, image, center_pygame, angle_radians):
    rotated = pygame.transform.rotate(image, math.degrees(angle_radians))
    rect = rotated.get_rect(center=center_pygame)
    screen.blit(rotated, rect)

def draw_moto_placeholder(screen, moto, camera_x, camera_y=0):  
    cw, ch = pm.moto_SIZE
    cos_a, sin_a = math.cos(moto.angle), math.sin(moto.angle)
    cx, cy = moto.position
    corners = []
    for x, y in [(-cw/2, -ch/2), (cw/2, -ch/2), (cw/2, ch/2), (-cw/2, ch/2)]:
        wx = cx + x*cos_a - y*sin_a
        wy = cy + x*sin_a + y*cos_a
        corners.append(to_pygame((wx, wy), camera_x, camera_y))
    pygame.draw.polygon(screen, (200, 40, 40), corners)
    pygame.draw.polygon(screen, (30, 0, 0), corners, 2)

def draw_rueda_placeholder(screen, body, camera_x, camera_y=0): 
    center = to_pygame(body.position, camera_x, camera_y)  
    pygame.draw.circle(screen, (35, 35, 35), center, pm.rueda_RADIUS)
    pygame.draw.circle(screen, (160, 160, 160), center, pm.rueda_RADIUS, 2)
    ex = center[0] + int(pm.rueda_RADIUS * math.cos(body.angle))
    ey = center[1] - int(pm.rueda_RADIUS * math.sin(body.angle))
    pygame.draw.line(screen, (255, 230, 60), center, (ex, ey), 2)

def draw_bike(screen, bike, lean_state, camera_x=0, camera_y=0):  
    assets = load_assets()
    rueda_img = assets.get('rueda')
    for w in bike['ruedas']:
        body = w['body']
        center = to_pygame(body.position, camera_x, camera_y)  
        if rueda_img is not None:
            blit_rotated(screen, rueda_img, center, body.angle)
        else:
            draw_rueda_placeholder(screen, body, camera_x, camera_y)

    moto = bike['moto']
    bike_key = {'back': 'bike_lean_back', 'fwd': 'bike_lean_fwd',
                'neutral': 'bike_neutral'}[lean_state]
    moto_img = assets.get(bike_key)
    center = to_pygame(moto.position, camera_x, camera_y)
    if moto_img is not None:
        blit_rotated(screen, moto_img, center, moto.angle)
    else:
        draw_moto_placeholder(screen, moto, camera_x, camera_y) 

def momento_angular_chasis(moto_body):
    return pm.moto_MOMENTO * moto_body.angular_velocity