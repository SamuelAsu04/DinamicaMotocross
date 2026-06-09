import random
import pygame # type: ignore
import pymunk # type: ignore

from confi import WIDTH, HEIGHT
from dibujado import  to_pygame

SEG_WIDTH      = 200
MARGEN_TERRENO  = 4000
SUELO_y       = 100
TERRAIN_MIN_Y  = SUELO_y - 10

# --- Suavidad del terreno normal (colinas redondeadas, no picos) ---
PEND_MAX     = 50     # pendiente máxima por tramo (px). Más alto = colinas más empinadas
PEND_CAMBIO  = 14     # cuánto varía la pendiente por tramo. MENOS = MÁS SUAVE (mando clave)
PEND_RETORNO = 0.05   # tirón hacia SUELO_y para que el terreno no se desboque

# --- Tipos de segmento (índices en propiedades_segmentos) ---
TIPO_NORMAL     = 0
TIPO_RAMPA      = 1   # colina suave (sube)
TIPO_ATERRIZAJE = 2   # colina suave (baja)
TIPO_KICKER     = 3   # labio de despegue del salto grande
TIPO_LANDING    = 4   # rampa de aterrizaje del salto grande

#  ( friccion, elesticidad, tipo de colision)
propiedades_segmentos = [
    (0.9,  0.15, 10),   # 0 NORMAL
    (0.7,  0.05, 11),   # 1 RAMPA suave
    (1.2,  0.05, 12),   # 2 ATERRIZAJE suave
    (0.95, 0.0,  11),   # 3 KICKER  -> colisión = rampa (11)
    (1.4,  0.0,  12),   # 4 LANDING -> colisión = aterrizaje (12), dispara tu impulso
]

# Colores por tipo: (relleno, borde). El salto se ve venir.
COLOR_TERRENO = ((55, 15, 10), (25, 5, 3))

# --- Salto grande (toque final: rampas para acrobacias en el aire) ---
# Geometría tabletop: carrerilla -> labio -> mesa plana -> aterrizaje en bajada.
RUNUP_SEGS   = 5      # tramos LLANOS antes del labio para coger velocidad
KICKER_SEGS   = 4     # tramos del labio. MÁS tramos = transición más curva/suave
KICKER_ALTURA = 280   # altura total del labio (px). Más alto = más aire
MESA_SEGS    = 1      # tramos planos en lo alto (la "mesa" del tabletop)
LANDING_SEGS = 3      # tramos de la rampa de aterrizaje (bajada hasta la base)
PROB_SALTO   = 0.4    # prob. de que un "evento" sea salto grande en vez de colina suave


class Terrain:
    def __init__(self, space):
        self.space = space
        self.segmentos = []
        self.frontier_x = -1000
        self.last_y = SUELO_y

        self.estado          = 0
        self.segs_en_estado  = 0
        self.segs_para_evento = random.randint(5, 9)
        self.pendiente        = 0.0    # pendiente actual del terreno normal (px/tramo)
        self.generar(MARGEN_TERRENO)

    def crear_segmento(self, x0, y0, x1, y1, tipo=0):
        shape = pymunk.Segment(self.space.static_body, (x0, y0), (x1, y1), 5)
        shape.friction, shape.elasticity, shape.collision_type = propiedades_segmentos[tipo]
        self.space.add(shape)
        self.segmentos.append({'shape': shape, 'x0': x0, 'y0': y0,
                               'x1': x1, 'y1': y1, 'tipo': tipo})

    def crear_salto_grande(self, x, y):
        """Construye un salto tipo tabletop completo y devuelve el (x, y) final.

        carrerilla (llano) -> labio (sube) -> mesa (plano) -> aterrizaje (baja).
        La carrerilla llana te deja acelerar limpio; despegas al final del labio,
        vuelas sobre la mesa y caes en la bajada. Siempre hay suelo continuo.
        """
        base = y

        # 0) Carrerilla: tramo llano y limpio para coger velocidad
        for _ in range(RUNUP_SEGS):
            next_x = x + SEG_WIDTH
            self.crear_segmento(x, base, next_x, base, TIPO_NORMAL)
            x = next_x
        y = base

        # 1) Labio de despegue: arranca casi plano (enlaza con la carrerilla)
        #    y se va empinando. La subida por tramo crece linealmente -> curva suave.
        denom = KICKER_SEGS * (KICKER_SEGS + 1) / 2     # 1+2+...+N
        for i in range(1, KICKER_SEGS + 1):
            next_x = x + SEG_WIDTH
            next_y = y + KICKER_ALTURA * i / denom      # tramos cada vez más empinados
            self.crear_segmento(x, y, next_x, next_y, TIPO_KICKER)
            x, y = next_x, next_y
        pico = y

        # 2) Mesa superior: tramo plano en lo alto (el borde de despegue)
        for _ in range(MESA_SEGS):
            next_x = x + SEG_WIDTH
            self.crear_segmento(x, y, next_x, y, TIPO_KICKER)
            x = next_x

        # 3) Rampa de aterrizaje: baja desde el pico hasta la base exacta
        caida = (pico - base) / LANDING_SEGS
        for _ in range(LANDING_SEGS):
            next_x = x + SEG_WIDTH
            next_y = y - caida
            self.crear_segmento(x, y, next_x, next_y, TIPO_LANDING)
            x, y = next_x, next_y

        return x, y

    def generar(self, target_x):
        x, y = self.frontier_x, self.last_y
        while x < target_x:

            # Bloque de salto grande: se construye de golpe
            if self.estado == 3:
                x, y = self.crear_salto_grande(x, y)
                self.estado = 0
                self.segs_en_estado = 0
                self.segs_para_evento = random.randint(6, 12)
                self.pendiente = 0.0
                continue

            next_x = x + SEG_WIDTH

            if self.estado == 1:
                next_y = y + random.uniform(60, 100)
            elif self.estado == 2:
                next_y = y + random.uniform(-120, -20)
            else:
                # Terreno normal: la PENDIENTE cambia poco a poco -> colinas suaves
                self.pendiente += random.uniform(-PEND_CAMBIO, PEND_CAMBIO)
                self.pendiente -= (y - SUELO_y) * PEND_RETORNO     # tirón a la base
                self.pendiente = max(-PEND_MAX, min(PEND_MAX, self.pendiente))
                next_y = y + self.pendiente

            next_y = max(TERRAIN_MIN_Y, next_y)

            self.crear_segmento(x, y, next_x, next_y, self.estado)
            self.siguiente_estado()
            x, y = next_x, next_y

        self.frontier_x = x
        self.last_y = y

    def update(self, moto_x):
        if self.frontier_x < moto_x + MARGEN_TERRENO:
            self.generar(moto_x + MARGEN_TERRENO)
        cutoff = moto_x - 20000
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
            relleno, borde = COLOR_TERRENO
            pygame.draw.polygon(screen, relleno,
                                [(sx0, sy0), (sx1, sy1), (sx1, HEIGHT), (sx0, HEIGHT)])
            pygame.draw.line(screen, borde, (sx0, sy0), (sx1, sy1), 4)

    def siguiente_estado(self):
        self.segs_en_estado += 1

        if self.estado == 0:
            if self.segs_en_estado >= self.segs_para_evento:
                # Elegir: salto grande (3) o colina suave (1)
                self.estado = 3 if random.random() < PROB_SALTO else 1
                self.segs_en_estado = 0

        elif self.estado == 1:
            if self.segs_en_estado >= 3:
                self.estado = 2
                self.segs_en_estado = 0

        elif self.estado == 2:
            if self.segs_en_estado >= 5:
                self.estado = 0
                self.segs_en_estado = 0
                self.segs_para_evento = random.randint(6, 12)
                self.pendiente = 0.0

    def altura_en(self, x):
        for s in self.segmentos:
            if s['x0'] <= x <= s['x1']:
                t = (x - s['x0']) / (s['x1'] - s['x0'])
                return s['y0'] + t * (s['y1'] - s['y0'])
        return self.last_y