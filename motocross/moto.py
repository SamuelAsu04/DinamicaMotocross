import math
import pygame # type: ignore
import pymunk # type: ignore
import propiedades_moto as pm
from confi import WIDTH, HEIGHT,FPS


class Moto:
    def __init__(self, space, position):
        px, py = position
        self.spawn = (px, py)
        self.aire  = False
        self.colisiones_ruedas = 0

        cw, ch = pm.moto_SIZE
        self.body = pymunk.Body(pm.moto_MASS, pymunk.moment_for_box(pm.moto_MASS, (cw, ch)))
        self.body.position = px, py
        shape = pymunk.Poly.create_box(self.body, (cw, ch))
        shape.friction    = 0.4
        shape.elasticity  = 0.1
        shape.collision_type = pm.moto_propiedades[2]
        shape.filter      = pymunk.ShapeFilter(group=1)
        space.add(self.body, shape)

        self.ruedas = []
        for side, offset_x in [(1, -pm.rueda_OFFSET_X), (2, pm.rueda_OFFSET_X)]:
            rueda = pymunk.Body(pm.rueda_MASS,
                                pymunk.moment_for_circle(pm.rueda_MASS, 0, pm.rueda_RADIUS))
            rueda.position = px + offset_x, py - pm.SUSPENSION_LENGTH

            rueda_shape = pymunk.Circle(rueda, pm.rueda_RADIUS)
            rueda_shape.friction        = pm.rueda_FRICTION
            rueda_shape.elasticity      = pm.rueda_ELASTICITY
            rueda_shape.collision_type  = side
            rueda_shape.filter          = pymunk.ShapeFilter(group=1)
            space.add(rueda, rueda_shape)

            groove = pymunk.GrooveJoint(
                self.body, rueda,
                (offset_x, 10), (offset_x, -pm.SUSPENSION_LENGTH - 10), (0, 0),
            )
            spring = pymunk.DampedSpring(
                self.body, rueda, (offset_x, 0), (0, 0),
                pm.SUSPENSION_LENGTH, pm.SUSPENSION_STIFFNESS, pm.SUSPENSION_DAMPING,
            )
            space.add(groove, spring)
            self.ruedas.append({'body': rueda, 'shape': rueda_shape, 'side': side, 'offset_x': offset_x})

    def reset(self, position=None):
        px, py = position if position is not None else self.spawn
        self.body.position         = px, py
        self.body.velocity         = (0, 0)
        self.body.angle            = 0
        self.body.angular_velocity = 0
        for w in self.ruedas:
            w['body'].position         = px + w['offset_x'], py - pm.SUSPENSION_LENGTH
            w['body'].velocity         = (0, 0)
            w['body'].angle            = 0
            w['body'].angular_velocity = 0
            
    def momento_angular(self):
        """L_z del sistema (chasis + 2 ruedas) respecto a su CM. Se conserva en el aire."""
        bodies = [self.body] + [w['body'] for w in self.ruedas]
        M   = sum(b.mass for b in bodies)
        cmx = sum(b.mass * b.position.x for b in bodies) / M
        cmy = sum(b.mass * b.position.y for b in bodies) / M
        vcx = sum(b.mass * b.velocity.x for b in bodies) / M
        vcy = sum(b.mass * b.velocity.y for b in bodies) / M
        L = 0.0
        for b in bodies:
            rx, ry = b.position.x - cmx, b.position.y - cmy
            vx, vy = b.velocity.x - vcx, b.velocity.y - vcy
            L += b.moment * b.angular_velocity + (rx * vy - ry * vx) * b.mass
        return L
    
    def set_patinaje(self, patinando: bool):
        """Cambia µ de la rueda trasera según si patina o no."""
        rueda_trasera = self.ruedas[0]  # side=1 es la trasera
        if patinando:
            rueda_trasera['shape'].friction = pm.rueda_FRICTION_DIN
        else:
            rueda_trasera['shape'].friction = pm.rueda_FRICTION
            
    def patina_trasera(self):
        """True si la rueda trasera desliza respecto al suelo (slip > umbral)."""
        rear   = self.ruedas[0]['body']
        v_sup  = abs(rear.angular_velocity) * pm.rueda_RADIUS
        v_moto = self.body.velocity.length
        return (v_sup - v_moto) > pm.SLIP_UMBRAL

    def aplicar_par_rueda(self, T):
        """Tierra: par motor SOLO a la rueda. El caballito emerge de la traccion via el eje."""
        self.ruedas[0]['body'].torque += -T      # -T => la rueda rueda hacia +x (avance)

    def aplicar_par_aire(self, tau):
        """Aire: par INTERNO chasis<->rueda. L del sistema se conserva (3a ley)."""
        self.body.torque              += +tau
        self.ruedas[0]['body'].torque += -tau