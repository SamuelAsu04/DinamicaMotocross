import math

import pygame
import pymunk
import pymunk.pygame_util
from fisica import Aerodinamica, Colision, TiroParabolico, Rotacion, MomentoInercia


# Configuración de la ventana
WIDTH, HEIGHT = 1000, 600
FPS = 60
NIVEL_DEL_SUELO=HEIGHT-60 #PIXELES 


#escala
PX_M=5 #5px por metro
M_PX=1.0/PX_M

#------------------------------------
RADIO_M=0.0213  #2.13 cm
HOYO_M=181.6    #coordenada X del hoyo

"""
    Vértices de una cabeza de palo de golf centrados en el CM.
    Listos para pymunk.Poly(body, vertices).

    Coordenadas locales con Y hacia ABAJO (convenio pymunk/pygame):
      p0 = borde líder  (abajo-izquierda, donde cara toca suela)
      p1 = talón        (abajo-derecha, parte trasera de la suela)
      p2 = trasera alta (arriba-derecha)
      p3 = cara alta    (arriba-izquierda, desplazada según loft)

    Parámetros
    ----------
    loft_deg       : ángulo de loft en grados (Driver=11, 5-iron=27...)
    longitud_suela : ancho de la suela [px]
    altura_cara    : altura de la cara de golpeo [px]
    altura_trasera : altura de la parte trasera [px]
"""

def vertices_cabeza_palo(loft_deg: float,
                          longitud_suela: float = 60.0,
                          altura_cara: float = 40.0,
                          altura_trasera: float = 32.0,
                          espejo: bool = False) -> list[tuple[float, float]]:
   
    a  = math.radians(loft_deg)
    W  = longitud_suela
    Hf = altura_cara
    Hb = altura_trasera

    p0 = (0.0,   0.0)
    p1 = (W,     0.0)
    p2 = (W,    -Hb)
    p3 = (Hf * math.sin(a), -Hf * math.cos(a))

    vertices = [p0, p1, p2, p3]    
    vertices = [(-x, y) for x, y in vertices]

    return _centrar(vertices)
def _centrar(vertices):
    """Centra los vértices restando el centroide exacto del polígono."""
    n    = len(vertices)
    area = cx = cy = 0.0
    for i in range(n):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % n]
        a    = x1*y2 - x2*y1
        area += a
        cx   += (x1 + x2) * a
        cy   += (y1 + y2) * a
    area *= 0.5
    cx   /= 6.0 * area
    cy   /= 6.0 * area
    return [(x - cx, y - cy) for x, y in vertices]

def dibujar_cabeza_palo(screen, body, shape, color=(50, 50, 50)):
    # Transforma cada vértice local → coordenadas mundo
    puntos = [body.local_to_world(v) for v in shape.get_vertices()]
    puntos_px = [(int(p.x), int(p.y)) for p in puntos]
    
    pygame.draw.polygon(screen, color, puntos_px)
    pygame.draw.polygon(screen, (0, 0, 0), puntos_px, 2)  # borde

def run():
	# 1. Inicializar Pygame
	pygame.init()
	screen = pygame.display.set_mode((WIDTH, HEIGHT))
	clock = pygame.time.Clock()
	draw_options = pymunk.pygame_util.DrawOptions(screen)
	bg_pos = (0,0)			
	# 2. Cargar y ajustar imagen de fondo
	# Cargamos la imagen y la escalamos para que cubra los 1000px de ancho
	try:
		bg_image = pygame.image.load("calle_golf.png")
		bg_width, bg_height = bg_image.get_size()
		bg_width*=0.7
		bg_height*=0.6
		# Ajuste proporcional: el ancho es 1000, calculamos el alto correspondiente
		aspect_ratio = bg_height / bg_width
		new_height = int(WIDTH * aspect_ratio)
		bg_image = pygame.transform.scale(bg_image, (WIDTH, new_height))
		# Posición: pegado a la parte inferior
		bg_pos = (0, HEIGHT - new_height)
	except pygame.error:
		print("No se pudo cargar la imagen calle_golf.png. Se usará fondo negro.")
		bg_image = None

	# 3. Inicializar Pymunk (Espacio físico)
	space = pymunk.Space()
	space.gravity = (0, 900)  # Gravedad hacia abajo (ajusta el valor según tu escala)

	# Creamos el suelo

	suelo = pymunk.Segment(space.static_body, (0, NIVEL_DEL_SUELO), (WIDTH, NIVEL_DEL_SUELO), 5)

	# Creamos el baston  

	masa_baston = 0.282
	vertices_baston = vertices_cabeza_palo(43, longitud_suela=20, altura_cara=10)
	momento_baston = MomentoInercia.poligono(masa_baston, vertices_baston)
	body_baston = pymunk.Body(masa_baston,momento_baston)
	body_baston.position = (0, NIVEL_DEL_SUELO - 50 - RADIO_M * PX_M)
	body_baston.velocity = (800,0)
	shape_baston = pymunk.Poly(body_baston,vertices_baston)
	# Creamos la bola 

	masa_bola = 0.045  # kg
	momento_bola = MomentoInercia.esfera_solida(masa_bola, RADIO_M)
	print(momento_bola)
	bola_body = pymunk.Body(masa_bola, momento_bola)
	bola_body.position = (100, NIVEL_DEL_SUELO - 50 - RADIO_M * PX_M)

	shape_bola = pymunk.Circle(bola_body, RADIO_M * PX_M)
	
	shape_bola.elasticity   = 0.6
	shape_bola.friction     = 0.5
	shape_baston.elasticity = 0.6
	shape_baston.friction   = 0.5
	suelo.elasticity        = 0.4
	suelo.friction          = 0.1

	space.add(suelo)
	space.add(bola_body, shape_bola)
	space.add(body_baston, shape_baston)
	

	# 4. Bucle principal de simulación
	running = True
	while running:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False

		# Limpiar pantalla
		screen.fill((135, 206, 235))  # Color cielo por defecto


		# Dibujar fondo si existe
		if bg_image:
			screen.blit(bg_image, bg_pos)

		# Paso de tiempo de la física (fijo para estabilidad)
		dt = 1.0 / FPS
		space.step(dt)

		# Dibujar debug de Pymunk (para ver los cuerpos físicos sobre el dibujo)
		# space.debug_draw(draw_options)


		radio=RADIO_M*PX_M*30
		pygame.draw.circle(screen, (255,255,255), bola_body.position, radio)
		
		pygame.draw.circle(screen, (255,255,255), (HOYO_M*PX_M,NIVEL_DEL_SUELO-radio), radio)
		
		dibujar_cabeza_palo(screen, body_baston,shape_baston, (0,0,255))
		pygame.draw.line(screen,(0,0,0), (0, NIVEL_DEL_SUELO), (WIDTH, NIVEL_DEL_SUELO), 2)
		pygame.display.flip()
		clock.tick(FPS)
		
		
		

	pygame.quit()

if __name__ == "__main__":
	run()
