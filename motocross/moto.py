import math
import pygame # type: ignore
import pymunk # type: ignore
import propiedades_moto as pm

WIDTH, HEIGHT = 1200, 600
FPS = 60

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
            self.ruedas.append({'body': rueda, 'side': side, 'offset_x': offset_x})

        rear_rueda  = self.ruedas[0]['body']
        self.motor  = pymunk.SimpleMotor(self.body, rear_rueda, 0)
        self.motor.max_force = 0
        space.add(self.motor)

    def reset(self):
        px, py = self.spawn
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
        "L = I · ω"
        return pm.moto_MOMENTO * self.body.angular_velocity