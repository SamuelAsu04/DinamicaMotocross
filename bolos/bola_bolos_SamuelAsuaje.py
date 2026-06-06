''' Una bola de bolos empieza deslizando hasta que, por rozamiento, su
velocidad disminuye y alcanza la rodadura pura.
Se puede cambiar el rozamiento y la velocidad inicial para ver cómo afecta'''

import pymunk 
import pymunk.pygame_util
import pygame
import math

# --- PARÁMETROS EDITABLES ---
MASA = 10.0					
RADIO = 45.0	
LADO=2*RADIO			
FRICCION_SUELO = 0.5
FRICCION_BOLA = 0.2

muk =FRICCION_SUELO*FRICCION_BOLA #coef. rozamiento μ 

VELOCIDAD_MAGNITUD = 500.0	# Rapidez inicial a lo largo del plano
GRAVEDAD = 981.0			
ANGULO_GRADOS = 0.0		# Inclinación de la rampa

# --- CONFIGURACIÓN DE PANTALLA ---
ANCHO = 1720
ALTO = 400					

tiempo_rodadura = (2/7)*((VELOCIDAD_MAGNITUD)/(muk*GRAVEDAD))
print("Prediccion tiempo: ", tiempo_rodadura )
velocidad_deslizamiento = VELOCIDAD_MAGNITUD-(muk*GRAVEDAD*tiempo_rodadura)
print("Prediccion velocidad: ", velocidad_deslizamiento)

# Puntos de la rampa (Descendente de derecha a izquierda)
angulo_rad = math.radians(ANGULO_GRADOS)
p1 = (ANCHO, ALTO - 50 -ALTO*math.sin(angulo_rad))	# Punto alto
p2 = (0, ALTO - 50)			# Punto bajo
grosor = ALTO
vertices = [
        p1,
        p2,
        (p2[0], p2[1] + grosor),
        (p1[0], p1[1] + grosor)
    ]

def setup_simulation(objeto):
	space = pymunk.Space()
	space.gravity = (0, GRAVEDAD)

	# --- EL PLANO INCLINADO ---
	static_body = space.static_body
    
	floor = pymunk.Poly(static_body, vertices)
	floor.friction = FRICCION_SUELO
	space.add(floor)

	# --- CÁLCULO DE POSICIÓN Y VELOCIDAD INICIAL ---
	# Vector dirección del plano (de p1 a p2)
	dx = p2[0] - p1[0]
	dy = p2[1] - p1[1]
	dist = math.sqrt(dx**2 + dy**2)
	ux, uy = dx/dist, dy/dist  # Vector unitario dirección plano
	
	# Vector normal al plano (hacia arriba/izquierda)
	nx, ny = -uy, ux
	
	# Posición: Punto de inicio p1 + desplazar hacia abajo el radio en la normal
	# y un poco hacia el centro para que no empiece en el borde exacto
	pos_x = p1[0] + ux * 100 + nx * RADIO
	pos_y = p1[1] + uy * 100 + ny * RADIO


	if objeto=='bola':
		# --- LA BOLA ---
		#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
		moment = (2/5) * MASA * (RADIO**2)
		bola = pymunk.Body(MASA, moment)
		bola.position = (pos_x, pos_y)
		
		# Velocidad inicial puramente en la dirección del plano
		bola.velocity = (ux * VELOCIDAD_MAGNITUD, uy * VELOCIDAD_MAGNITUD)
		
		# Ángulo inicial alineado con la rampa
		bola.angle = math.atan2(dy, dx)
		
		shape_bola = pymunk.Circle(bola, RADIO)
		shape_bola.friction = FRICCION_BOLA
		
		space.add(bola, shape_bola)
		return space,bola
	
def main():
	pygame.init()
	screen = pygame.display.set_mode((ANCHO, ALTO))
	pygame.display.set_caption("Bola de bolos - Apartado 2")
	clock = pygame.time.Clock()
	draw_options = pymunk.pygame_util.DrawOptions(screen)

	space,body = setup_simulation('bola')

	font = pygame.font.SysFont("Verdana", 20, True)

	tiempo=0
	tiempo_rod = 0
	Estado = "Deslizamiento"
	running = True
	while running:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False

		screen.fill(((29, 29, 51)))
		space.debug_draw(draw_options)
		pygame.draw.polygon(screen, (210, 180, 140), vertices)

		
		vx, vy = body.velocity
		if 0 <= body.position.x <= ANCHO and 0 <= body.position.y <= ALTO:
			if(Estado == "Deslizamiento"): tiempo_rod = tiempo 
			elif(Estado == "Rodadura Pura"): tiempo_rod = tiempo_rod
			tiempo += 1 / 60.0
			velocidad = math.sqrt(vx**2 + vy**2)
			velocidad_angular = body.angular_velocity
			if( velocidad - abs(velocidad_angular*RADIO) < 1):
				Estado = "Rodadura Pura"
		else:
			# Mantener los valores actuales, no actualizarlos
			Estado = Estado
			velocidad = velocidad
			velocidad_angular = velocidad_angular
			
	# --- TEXTO ESQUINA IZQUIERDA ---
		info_izquierda = [ "Samuel Asuaje",
			f"Tiempo: {tiempo:.2f}",
			f"Tiempo de Rodadura: {tiempo_rod:.2f}",
			f"Velocidad: {velocidad:.2f}",
			f"Velocidad Angular: {abs(velocidad_angular):.2f}",
			f"Estado:  {Estado}"
		]
		for i, text in enumerate(info_izquierda):
			if(text== "Samuel Asuaje"):
				color = (200,0,0)
			elif Estado == "Rodadura Pura" and ("Velocidad:" in text or "Tiempo de Rodadura" in text):
					color = (0, 200, 0)  # verde
			else:
					color = (255, 255, 255)    # negro por defecto
			render = font.render(text, True, color)
			screen.blit(render, (10, 10 + i * 25))

		# --- TEXTO ESQUINA DERECHA ---
		info_derecha = [
			f"Prediccion tiempo rodadura: {tiempo_rodadura:.2f}",
			f"Prediccion velocidad: {velocidad_deslizamiento:.2f}"
		]
		for i, text in enumerate(info_derecha):
			render = font.render(text, True, (241, 110, 255))
			text_width = render.get_width()
			screen.blit(render, (ANCHO - text_width - 10, 10 + i * 25))
		
		# Paso de física
		space.step(1/60.0)
		
		pygame.display.flip()
		clock.tick(60)

	pygame.quit()

if __name__ == "__main__":
	main()
