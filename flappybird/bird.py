from .sprites import BaseSprite, html_color
from . import gllib as gl
from . import config
import numpy as np
import math

class Bird(BaseSprite):
    maskColors = list(map(html_color, [
        'd4bf27', 'dfc719', 'c4b867', 'dfc719'
    ]))

    MAX_ANGLE = 0.4
    SHAPE_RADIUS_A = 8
    SHAPE_RADIUS_B = 6

    def __init__(self):
        self.currentFrame = 0
        self.effects = []
        self._screenPos = np.array(config.birdInitPos, dtype=gl.GLfloat)
        self.speed = [config.scrollDistancePerFrame, 0]
        self._flapColdDown = self._flapColdDOwn0 = config.FPS // 12
        self.started = False
        self._hit = False
        self._tick = 0
        self._flapGainColdDown = config.speedGainColdDown

    @property
    def maskColor(self):
        return self.maskColors[self.currentFrame]

    def on_hit(self):
        self._hit = True

    def flap(self):
        if self._flapGainColdDown == 0 and self.screenPos[1] < config.screenHeight / 2:
            self.speed[1] = 0
            self._flapGainColdDown = config.speedGainColdDown

    def update(self, dt):
        self.update_effects(dt)
        if not self.started:
            self.angle = 0.
            T = config.FPS / 1.5
            self._tick = (self._tick + 1) % T
            self.screenPos[1] = math.sin(math.pi * 2 * self._tick / T) * 2
        else:
            vx, vy = self.speed
            self.angle = min(self.MAX_ANGLE, math.atan2(vy, vx))
            self.screenPos[1] += vy
            self.speed[1] -= config.gravity
            if self._flapGainColdDown > 0:
                self.speed[1] += self._flapGainColdDown * 0.08
                self._flapGainColdDown -= 1
            self.speed[1] = np.clip(
                self.speed[1], -config.maxDownSpeed, config.maxUpSpeed)
        if self.angle < 0 or self._hit:
            self.currentFrame = 1
        else:
            self._flapColdDown -= 1
            if self._flapColdDown == 0:
                self._flapColdDown = self._flapColdDOwn0
                self.currentFrame = (1 + self.currentFrame) % len(self.maskColors)

    def get_pixels(self):
        a = np.arange(0, np.pi, np.pi / 50)
        xs = self.SHAPE_RADIUS_A * np.cos(a)
        ys = self.SHAPE_RADIUS_B * np.sin(a)
        c = np.cos(self.angle)
        s = np.sin(self.angle)
        x0, y0 = self.screenPos
        xs1 = xs * c - ys * s + x0
        ys1 = xs * s + ys * c + y0
        return np.vstack([xs1, ys1]).T
