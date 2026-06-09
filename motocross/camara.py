import math
import sys
import pygame
import pymunk
from confi import WIDTH, HEIGHT
 
CAMERA_OFFSET_X = WIDTH // 3
CAMERA_OFFSET_Y = HEIGHT // 3
 
# --- Zoom ---
ZOOM_SUELO  = 1.0   
ZOOM_AIRE   = 0.7    
ZOOM_LERP   = 0.08   
ALTURA_ZOOM = 300    
 
 
class Camera():
 
    def __init__(self):
        self.x    = 0.0
        self.y    = 0.0
        self.zoom = 1.0
 
    def actu_camara(self, x, y, altura=0.0):
        self.x += (x - CAMERA_OFFSET_X - self.x) * 0.12
        self.y += (y - CAMERA_OFFSET_Y - self.y) * 0.12
 
        objetivo = ZOOM_AIRE if altura > ALTURA_ZOOM else ZOOM_SUELO
        self.zoom += (objetivo - self.zoom) * ZOOM_LERP
 