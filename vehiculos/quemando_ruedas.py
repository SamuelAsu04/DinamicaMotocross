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
def friccion_maxima_f430(mu,v,masa=1400,angulo=0):
	#tiene en cuenta la carga aerodinámica
	fc=carga_aerodinamica_f430(v)
	fN=masa*9.81*np.cos(np.radians(angulo))+fc
	return fN*mu
#--------------------------------------------------

########################################################################
########################################################################


ACELERADOR=0
FRENO=0
MARCHA=1


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


dt=1/600
masa=1450 #kg
I_rueda=40   #pongo la del motor tb 2.5
radio_rueda=0.38
w_rueda=0
v_coche=0
tiempo=0
rpm=4000
mu=1.0 #rozamiento real puede ser 1 -1.2
mu_din=mu*0.75
ACELERADOR=1.0
#w_rueda=rpm*2*np.pi/60
w_rueda = (rpm * 2 * np.pi) / (60 * (3.29 * 4.30))
while sim.actualizar_eventos():
	for _ in range(10):    
		
		
		frmax = friccion_maxima_f430(mu, v_coche)       #tiene en cuenta la carga aerodinámica        
		ft = ACELERADOR * fuerza_empuje(rpm, MARCHA)
		fd = fuerza_aire_f430(v_coche)
		fr = fuerza_rodadura_f430()
		if ACELERADOR == 0: 
			fm = fuerza_freno_motor(rpm, MARCHA)
		else:
			fm = 0
		#---------------------------------
		
		# Cuando patina, la fuerza de tracción real que impulsa al coche es la fricción dinámica
		frmax_din = friccion_maxima_f430(mu_din, v_coche)
		
		if ft <= frmax:
			# RODADURA PURA: El coche y la rueda aceleran juntos
			ft_real = ft
			f_exc = 0
			a_coche = (ft_real - fd - fr - fm) / masa
			v_coche += dt * a_coche
			
			w_rueda = v_coche / radio_rueda
			alpha_rueda = a_coche / radio_rueda
		else:    
			# PATINA: La rueda se embala y el coche se mueve solo por la fuerza dinámica
			print('PATINA --- ', end='')
			ft_real = frmax_din
			f_exc = ft - ft_real
			
			a_coche = (ft_real - fd - fr - fm) / masa
			v_coche += dt * a_coche
			
			# Aceleración angular debida al exceso de torque aplicado en el eje
			# T_neto = T_motor - F_friccion * R. Como ft = T_motor / R -> T_neto = (ft - ft_real) * R
			alpha_rueda = (ft - ft_real) * radio_rueda / I_rueda
			w_rueda += dt * alpha_rueda
			
			# Condición de retorno: si la rueda se frena (o el coche acelera) y se igualan
			if w_rueda * radio_rueda <= v_coche:
				w_rueda = v_coche / radio_rueda
				rpm = rpm_velocidad_f430(v_coche, MARCHA)
		
		v_coche = max(0, v_coche)
		
		# Las RPM del motor siguen estrictamente la velocidad de la rueda girando
		rpm = min(rpm_velocidad_f430(w_rueda * radio_rueda, MARCHA), 8500)
		if rpm>8000: MARCHA+=1
		if rpm < 1000: rpm = 1000 # Evitamos que el motor baje del ralentí ideal si se frena
		
		time.sleep(dt)
		
		tiempo += dt
		print(f'Velocidad: {v_coche*3.6:.2f} ', end='') 
		print(f'Marcha: {MARCHA} ', end='') 
		print(f'Tracción: {ft_real:.2f} ', end='') 
		print(f'Exceso: {f_exc:.2f} ', end='') 
		print(f'Alpha R: {alpha_rueda:.2f} ', end='') 
		print(f'Omega R: {w_rueda:.2f} ', end='') 
		print(f'RPM: {rpm:.0f} ', end='') 
		print(f'T: {tiempo:.4f} ')
		
		if (v_coche*3.6>100):
			while True:
				continue
		
	#--if v_coche>50/3.6: ACELERADOR=0
	#if (w_rueda*radio_rueda>v_coche):
	#print("\033[31mDERRAPA\033[0m")
	#print(f'{ft_real:.0f} {f_exc:.0f} {ft_real:.0f} {f_exc:.0f} {alpha_rueda:.0f}')
	#print(f'Velocidad: {v_coche*3.6:.2f} {w_rueda*radio_rueda:.2f} km/h {rpm:8.0f} r.p.m. Marcha: {MARCHA} Acelerador: {ACELERADOR*100:5.0f} %')
	#else:	
	#	print(f'Velocidad: {v_coche*3.6:.2f} {w_rueda*radio_rueda:.2f} km/h {rpm:8.0f} r.p.m. Marcha: {MARCHA} Acelerador: {ACELERADOR*100:5.0f} %')
	
	

