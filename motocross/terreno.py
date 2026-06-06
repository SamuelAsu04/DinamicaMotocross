import random
import pygame
import pymunk

from moto import WIDTH, HEIGHT, to_pygame

SEG_WIDTH      = 200
MARGEN_TERRENO  = 4000
SUELO_y       = 100
TERRAIN_AMP    = 85
TERRAIN_MIN_Y  = SUELO_y - 10


class Terrain:
    def __init__(self, space):
        self.space = space
        self.segmentos = []
        self.frontier_x = -1000
        self.last_y = SUELO_y
        self.generate_up_to(MARGEN_TERRENO)

    def crear_segmento(self, x0, y0, x1, y1):
        shape = pymunk.Segment(self.space.static_body, (x0, y0), (x1, y1), 5)
        shape.friction = 1.0
        shape.elasticity = 0.2
        self.space.add(shape)
        self.segmentos.append({'shape': shape, 'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1})

    def generate_up_to(self, target_x):
        x, y = self.frontier_x, self.last_y
        while x < target_x:
            next_x = x + SEG_WIDTH
            next_y = max(TERRAIN_MIN_Y, y + random.uniform(-TERRAIN_AMP, TERRAIN_AMP))
            self.crear_segmento(x, y, next_x, next_y)
            x, y = next_x, next_y
        self.frontier_x = x
        self.last_y = y

    def update(self, moto_x):
        if self.frontier_x < moto_x + MARGEN_TERRENO:
            self.generate_up_to(moto_x + MARGEN_TERRENO)
        cutoff = moto_x - 20000 # espacio trasero
        to_remove = [s for s in self.segmentos if s['x1'] < cutoff]
        for s in to_remove:
            self.space.remove(s['shape'])
            self.segmentos.remove(s)

    def draw(self, screen, camera_x, camera_y=0):
        for s in self.segmentos:
            sx0, sy0 = to_pygame((s['x0'], s['y0']), camera_x, camera_y)
            sx1, sy1 = to_pygame((s['x1'], s['y1']), camera_x, camera_y)
            if sx1 < -50 or sx0 > WIDTH + 50:
                continue
            pygame.draw.polygon(screen, (110, 80, 50),
                                [(sx0, sy0), (sx1, sy1), (sx1, HEIGHT), (sx0, HEIGHT)])
            pygame.draw.line(screen, (80, 55, 30), (sx0, sy0), (sx1, sy1), 4)