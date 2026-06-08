import math
import pygame
import pymunk

moto_SIZE   = (80, 70)
moto_MASS   = 150.0
moto_MOMENTO = pymunk.moment_for_box(moto_MASS, moto_SIZE)
rueda_RADIUS      = 16
rueda_MASS        = 15.0
rueda_FRICTION    = 1.2
rueda_ELASTICITY  = 0.2
rueda_OFFSET_X       = 36
rueda_FRICTION_DIN = 0.5   # µ dinámico (~40% menos)
MOTOR_RATE_PATINAJE = 80   # velocidad angular que dispara el patinaje

TORQUE_AIRE     = 300_000   # torque que puede aplicar el piloto en el aire (menor que en suelo)
OMEGA_MAX_AIRE  = 4.0      # límite de velocidad angular en el aire [rad/s]
ESTABILIZACION  = 100_000   # torque suave que intenta nivelar la moto al soltar controles
SUSPENSION_LENGTH    = 24
SUSPENSION_STIFFNESS = 30_000   
SUSPENSION_DAMPING   = 500      

rueda_SPRITE_DIAMETER = 2 * rueda_RADIUS + 4
BIKE_SPRITE_WIDTH     = 110

ruedas_propiedades = [1,2]