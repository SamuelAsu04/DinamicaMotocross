import math 
import pygame # type: ignore
import pymunk # type: ignore
import propiedades_moto as pm
from confi import WIDTH, HEIGHT,FPS


ASSET_PATHS = {
    'rueda':          'motocross/rueda.png',
    'bike_neutral':   'motocross/bike1.png',
    'bike_lean_back': 'motocross/bike3.png',
    'bike_lean_fwd':  'motocross/bike2.png',
}

ZOOM = 1.0

def scale_to_width(surface, target_width):
    w, h = surface.get_size()
    if w == 0:
        return surface
    target_height = max(1, int(h * target_width / w))
    return pygame.transform.smoothscale(surface, (target_width, target_height))

ASSETS = None  

def load_assets():
    global ASSETS
    if ASSETS is not None:         
        return ASSETS

    assets = {}
    for key, path in ASSET_PATHS.items():
        try:
            img = pygame.image.load(path).convert_alpha()
            target = pm.rueda_SPRITE_DIAMETER if key == 'rueda' else pm.moto_SPRITE_WIDTH
            assets[key] = scale_to_width(img, target)
        except (pygame.error, FileNotFoundError) as e:
            print(f"[aviso] No se pudo cargar '{path}' ({e}). Uso placeholder.")
            assets[key] = None

    ASSETS = assets                 
    return assets

def to_pygame(p, camera_x=0, camera_y=0):
    sx = p[0] - camera_x
    sy = HEIGHT - p[1] + camera_y
    cx, cy = WIDTH / 2, HEIGHT / 2          # centro = punto fijo del zoom
    return int(cx + (sx - cx) * ZOOM), int(cy + (sy - cy) * ZOOM)

# -----------------------------------------------------------------------------
# Dibujar
# -----------------------------------------------------------------------------
def blit_rotated(screen, image, center_pygame, angle_radians):
    rotated = pygame.transform.rotozoom(image, math.degrees(angle_radians), ZOOM)
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
    r = max(1, int(pm.rueda_RADIUS * ZOOM))
    pygame.draw.circle(screen, (35, 35, 35), center, r)
    pygame.draw.circle(screen, (160, 160, 160), center, r, 2)
    ex = center[0] + int(r * math.cos(body.angle))
    ey = center[1] - int(r * math.sin(body.angle))
    pygame.draw.line(screen, (255, 230, 60), center, (ex, ey), 2)

def draw_moto(screen, bike, lean_state, camera_x=0, camera_y=0):  
    assets = load_assets()
    rueda_img = assets.get('rueda')
    for w in bike.ruedas:
        body = w['body']
        center = to_pygame(body.position, camera_x, camera_y)  
        if rueda_img is not None:
            blit_rotated(screen, rueda_img, center, body.angle)
        else:
            draw_rueda_placeholder(screen, body, camera_x, camera_y)

    moto = bike.body
    bike_key = {'back': 'bike_lean_back', 'fwd': 'bike_lean_fwd',
                'neutral': 'bike_neutral'}[lean_state]
    moto_img = assets.get(bike_key)
    center = to_pygame(moto.position, camera_x, camera_y)
    if moto_img is not None:
        blit_rotated(screen, moto_img, center, moto.angle)
    else:
        draw_moto_placeholder(screen, moto, camera_x, camera_y) 

