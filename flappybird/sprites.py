import numpy as np
from . import gllib as gl
from .effects import FadeOut
from . import config

def init():
    pass


def html_color(c):
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))


class BaseSprite:
    angle = 0.
    alpha = 1.
    _needRemove = False

    def __init__(self, maskColor, screenPos):
        self.maskColor = maskColor
        self._screenPos = np.array(screenPos, dtype=gl.GLfloat)
        self.effects = []

    @property
    def screenPos(self):
        return self._screenPos

    @screenPos.setter
    def screenPos(self, pos):
        self._screenPos[:] = pos

    @staticmethod
    def make_simple_sprites(datas):
        """
        datas: [(name, maskColor, screenPos)]
        """
        sprites = {}
        for name, maskColor, screenPos in datas:
            sprites[name] = BaseSprite(maskColor, screenPos)
        return sprites

    def __repr__(self):
        return '{}(pos={})'.format(
            self.__class__.__name__, tuple(map(int, self.screenPos)))

    def add_effect(self, effectClass, *args):
        self.effects.append(effectClass(self, *args))

    def fade_out(self, on_finish):
        self.add_effect(FadeOut, on_finish)

    def update_effects(self, dt):
        for effect in self.effects:
            effect.update(dt)
        self.effects = [e for e in self.effects if not e.finished]

    def update(self, dt):
        self.update_effects(dt)

    def mark_to_remove(self):
        self._needRemove = True

    def __del__(self):
        print(self, '__del__')


class Sprite(BaseSprite):
    # Color on spritemask.png
    maskColor = None
    initScreenPos = (0, 0)

    def __init__(self):
        super().__init__(self.maskColor, self.initScreenPos)


class Background(Sprite):
    maskColor = html_color('70c5ce')


class Pillar(Sprite):
    offset = 0
    initY = 0


class LowerPillar(Pillar):
    maskColor = html_color('558022')
    initY = - (config.lowerPillarHeight + config.notchHeight) / 2


class UpperPillar(Pillar):
    maskColor = html_color('73bf2e')
    initY = (config.upperPillarHeight + config.notchHeight) / 2


class Floor(Sprite):
    maskColor = html_color('ded895')
    initScreenPos = (0, -103)
    moving = True
    _tick = 0

    def update(self, dt):
        if self.moving:
            self._tick += config.scrollDistancePerFrame
            self._tick %= 14
        self.screenPos[0] = (-self._tick) % 7 - 3
        super().update(dt)


class TapToStart(Sprite):
    maskColor = html_color('ff290d')
