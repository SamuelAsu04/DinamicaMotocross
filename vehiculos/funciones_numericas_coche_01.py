import numpy as np
import math
from scipy.interpolate import interp1d
from simulaciones_genericas import Tsim
import pygame,time


#--------------------------------------------
def par_potencia_ferrari_f430(rpm_consulta):
	"""
	Calcula el par motor (Nm) y la potencia (CV) del Ferrari F430 para unas RPM dadas.
	Utiliza interpolación de spline cúbica basada en datos técnicos reales.
	"""
	# Datos maestros del Ferrari F430 V8
	rpm_datos = np.array([1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 5250, 5500, 6000, 6500, 7000, 7500, 8000, 8500])
	par_datos = np.array([320, 345, 370, 400, 415, 430, 445, 455, 465, 465, 460, 455, 450, 440, 430, 415, 390])
	# Creamos la función de interpolación (spline cúbica)
	interp_par = interp1d(rpm_datos, par_datos, kind='cubic', fill_value="extrapolate")
	# 1. Calculamos el Par (T) para la consulta
	par = float(interp_par(rpm_consulta))
	# 2. Calculamos la Potencia (P) en CV
	potencia = (par * rpm_consulta * 2 * np.pi) / (60 * 735.5)
	return par, potencia
#---------------------------------------------
def velocidad_rpm_f430(rpm, marcha):
	if marcha < 1 or marcha > 6:
		return 0.0
	relaciones = {1: 3.29, 2: 2.16, 3: 1.61, 4: 1.26, 5: 1.03, 6: 0.85}
	final_drive = 4.30 # Relación del diferencial
	radio_rueda = 0.38 # metros
	reduccion_total = relaciones[marcha] * final_drive
	w_rueda = (rpm * 2 * np.pi) / (60 * reduccion_total)
	velocidad_ms = w_rueda * radio_rueda
	return velocidad_ms
#---------------------------------------------------
def rpm_velocidad_f430(v_ms, marcha):
	if marcha < 1 or marcha > 6 or v_ms <= 0:
		return 0.0

	relaciones = {1: 3.29, 2: 2.16, 3: 1.61, 4: 1.26, 5: 1.03, 6: 0.85}
	final_drive = 4.30
	radio_rueda = 0.38

	w_rueda = v_ms / radio_rueda
	reduccion_total = relaciones[marcha] * final_drive
	w_motor = w_rueda * reduccion_total
	rpm = (w_motor * 60) / (2 * math.pi)

	return rpm
#---------------------------------------------------
def fuerza_aire_f430(v_ms):
	rho = 1.225      # Densidad del aire en kg/m^3
	Cd = 0.33        # Coeficiente de arrastre del Ferrari F430
	area_frontal = 2.03 # Área frontal en metros cuadrados
	
	fuerza_drag = 0.5 * rho * (v_ms**2) * Cd * area_frontal
	return fuerza_drag
#---------------------------------------------------
def carga_aerodinamica_f430(v_ms):
	rho = 1.225         # Densidad del aire en kg/m^3
	Cl = 0.30           # Coeficiente de carga aerodinámica (downforce) del F430
	area_frontal = 2.03 # Área frontal en metros cuadrados
	
	# La ecuación matemática es la misma, cambia el coeficiente Cl
	fuerza_downforce = 0.5 * rho * (v_ms**2) * Cl * area_frontal
	return fuerza_downforce
#----------------------------------------------   
def fuerza_rodadura_f430(masa_kg=1450, incl_rad=0.0):
	mu_rr = 0.015 
	g = 9.81
	normal = masa_kg * g * math.cos(incl_rad)
	fuerza_rodadura = mu_rr * normal
	return fuerza_rodadura
#------------------------------------------------    
def fuerza_empuje(rpm, marcha):
	if marcha < 1 or marcha > 6:
		return 0.0
	torque_motor= par_potencia_ferrari_f430(rpm)[0]
	relaciones = {1: 3.29, 2: 2.16, 3: 1.61, 4: 1.26, 5: 1.03, 6: 0.85}
	final_drive = 4.30
	radio_rueda = 0.38
	eficiencia = 0.88 
	reduccion_total = relaciones[marcha] * final_drive
	fuerza = (torque_motor * reduccion_total * efficiency) / radio_rueda if 'efficiency' in locals() else (torque_motor * reduccion_total * eficiencia) / radio_rueda
	return fuerza
#-----------------------------------------
def fuerza_freno_motor(rpm, marcha):
	if marcha < 1: return 20  #rozamiento sólo de las piezas
	torque_resistencia_motor = 15 + (rpm * 0.01) 
	relaciones = {1: 3.29, 2: 2.16, 3: 1.61, 4: 1.26, 5: 1.03, 6: 0.85}
	final_drive = 4.30
	radio_rueda = 0.38
	reduccion_total = relaciones[marcha] * final_drive
	fuerza_freno = (torque_resistencia_motor * reduccion_total) / radio_rueda
	return fuerza_freno
#---------------------------------------------


########################################################################
########################################################################



ACELERADOR=0
FRENO=0
MARCHA=1
rpm=0

def acelera():
	global ACELERADOR
	ACELERADOR=min(ACELERADOR+0.05,1)
#--------------------------------------------			
def decelera():
	global ACELERADOR
	ACELERADOR=max(0,ACELERADOR-0.05)
#--------------------------------------------			
def marcha_up():
	global MARCHA
	MARCHA=min(MARCHA+1,6)
#--------------------------------------------		
def marcha_down():
	global MARCHA
	MARCHA=max(MARCHA-1,1)
		
	

sim=Tsim(height=200,width=200)
sim.add_evento_tecla(pygame.K_UP,acelera)
sim.add_evento_tecla(pygame.K_DOWN,decelera)
sim.add_evento_tecla(pygame.K_RIGHT,marcha_up)
sim.add_evento_tecla(pygame.K_LEFT,marcha_down)

dt=1/60

rpm=0
MARCHA=1
masa=1400
v=0
while sim.actualizar_eventos():
	
	ft=ACELERADOR*fuerza_empuje(rpm, MARCHA)
	fd=fuerza_aire_f430(v)
	fr=fuerza_rodadura_f430()
	
	fuerza=ft-fd-fr
	
	a=fuerza/masa
	
	v+=dt*a
	
	if v<0: v=0
	rpm=rpm_velocidad_f430(v, MARCHA)
	
	time.sleep(dt)
	
	print(v,rpm)


