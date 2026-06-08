import math
import sys
import pygame
import pymunk


WIDTH, HEIGHT = 1200, 600
FPS = 60

CAMERA_OFFSET_X = WIDTH // 3
CAMERA_OFFSET_Y = HEIGHT // 3

class Camera():

    def __init__(self):
        self.x    = 0.0
        self.y    = 0.0

    def actu_camara(self, x, y):
        self.x += (x - CAMERA_OFFSET_X - self.x) * 0.12
        self.y += (y - CAMERA_OFFSET_Y - self.y) * 0.12