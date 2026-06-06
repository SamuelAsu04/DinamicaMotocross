import os
import pygame
from pymunk import Vec2d
import pymunk

###################################################################################
class Tsim:
	def __init__(self,width=1000,height=600,suelo=600,PX_M=1,gravedad=(0,-9.81),fondo=None):
		'''' Esta clase es generica e implementa funciones para incluir manejo de teclas pulsadas'''
		self.width=width
		self.height=height
		self.PX_M=PX_M
		self.M_PX=1.0/PX_M
		self.suelo=	suelo
		#inicia pygame
		pygame.init()
		self.screen = pygame.display.set_mode((self.width, self.height))
		self.clock = pygame.time.Clock()
		#intenta poner el fondo
		if fondo!=None: 
			self.fondo=self.pone_fondo(fondo)
		else:
			self.fondo=None	
		#crea el espacio	
		self.space = pymunk.Space()
		self.space.gravity = Vec2d(gravedad[0],-gravedad[1])* PX_M
		self.space.iterations = 35 # Aumentamos iteraciones para mayor estabilidad	
		
		#lista de objetos
		#creo una lista de objetos donde automaticamente se van a ir poniendo todos los objetos
		#que se inserten en la simulación
		#este diccionario se va a recorrer por ejemplo para dibujar
		#cada objeto al crearse le pone el key que le digamos
		self.objetos=dict()
		
		# Diccionario: {tecla: {'func': funcion, 'activo': bool}}
		self._eventos_teclado = {}
		self.running = True
		
		
	#-------- pone imagen de fondo ----------------------------------	
	def pone_fondo(self,imagen):
		try:
			fondo = pygame.image.load(imagen).convert()
			fondo = pygame.transform.smoothscale(fondo, (self.width,self.height))
		except:
			fondo = None
			print('No se encuentra la imagen')
		self.fondo=fondo
		return fondo	
		
	#----------------------------------------------------------------------	
	def draw(self):
		if self.fondo: self.screen.blit(self.fondo, (0, 0))
		else: self.screen.fill((240, 240, 240))	
		for obj in self.objetos.values():
			obj.draw()
	#----------------------------------------------------------------------	
		
	#------------------- eventos ----------------------------
	def add_evento_tecla(self, tecla, funcion, activo=True):
		"""Registra una tecla con su función y estado inicial."""
		self._eventos_teclado[tecla] = {
			'func': funcion,
			'activo': activo}
	#-----------------------  on  / off------------------------------
	def set_estado_evento(self, tecla, estado):
		"""Activa o desactiva un evento específico."""
		if tecla in self._eventos_teclado:
			self._eventos_teclado[tecla]['activo'] = estado
	#------------------- manejador de eventos ----------------------
	def actualizar_eventos(self):
		"""Procesa eventos y ejecuta solo los que están activos."""
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				self.running = False
				return False
			
			if event.type == pygame.KEYDOWN:
				if event.key in self._eventos_teclado:
					evento = self._eventos_teclado[event.key]
					if evento['activo']:
						evento['func']()							
		return True
	#----------------------------------------------------------------

###############################################################################
###################################################################################
