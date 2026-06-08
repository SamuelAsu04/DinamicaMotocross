import math
import pygame   # type: ignore
import pymunk  # type: ignore


# CHASIS / MOTO

moto_SIZE    = (80, 70)
moto_MASS    = 150.0
moto_MOMENTO = pymunk.moment_for_box(moto_MASS, moto_SIZE)


# RUEDAS

rueda_RADIUS       = 16
rueda_MASS         = 15.0
rueda_FRICTION     = 1.2        # u estatico
rueda_FRICTION_DIN = 0.9        # u dinamico 
rueda_ELASTICITY   = 0.2
rueda_OFFSET_X     = 36
ruedas_propiedades = [1, 2]

# MOTOR y TRACCION

PAR_MOTOR           = 1200000  
FACTOR_TRACCION     = 0.4  
SLIP_UMBRAL         = 40       
MOTOR_RATE_PATINAJE = 80        

# CONTROL EN EL AIRE

PILOT_TORQUE   = 600_000  
OMEGA_MAX_AIRE = 4.0       

# SUSPENSION

SUSPENSION_LENGTH    = 24
SUSPENSION_STIFFNESS = 30_000
SUSPENSION_DAMPING   = 500

# INCLINACIOn

LEAN_TORQUE = 500_000  

# SPRITES 

rueda_SPRITE_DIAMETER = 2 * rueda_RADIUS + 4
moto_SPRITE_WIDTH     = 110
