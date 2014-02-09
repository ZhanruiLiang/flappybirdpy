import pyglet
from . import config
from . import sprites
from .render import Render
from . import gllib as gl
from .game import Game
from . import ui

class App(pyglet.window.Window):
    def __init__(self):
        super().__init__(
            caption=config.caption,
            resizable=False,
            width=config.screenWidth * config.zoom,
            height=config.screenHeight * config.zoom,
        )
        sprites.init()
        self.init_gl()
        self.render = Render()
        self._fbContext = None

        self.set_context(Game)
        pyglet.clock.schedule_interval(self.update, 1 / config.FPS)

    def set_context(self, contextClass):
        self._fbContext = contextClass(self)

    def init_gl(self):
        gl.glDisable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_TEXTURE_2D)
        gl.glClearColor(1., 1., 1., 1.)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

    def run(self):
        pyglet.app.run()

    def on_resize(self, w, h):
        self._width = w
        self._height = h
        gl.glViewport(0, 0, w, h)

    def on_draw(self):
        self.clear()
        R = self.render
        context = self._fbContext
        with R.batch_draw():
            R.draw_sprites(context.sprites)

    def convert_mouse_pos(self, x, y):
        x -= self._width / 2
        y -= self._height / 2
        x *= config.screenWidth / self._width
        y *= config.screenHeight / self._height
        return (x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        mouseScreenPos = self.convert_mouse_pos(x, y)
        for sp in self._fbContext.sprites:
            if isinstance(sp, ui.Button):
                if sp.in_rect(mouseScreenPos):
                    sp._on_click()
        self._fbContext.on_mouse_press(x, y, button, modifiers)

    def on_key_press(self, key, modifiers):
        if key == pyglet.window.key.ESCAPE:
            pyglet.app.exit()
        self._fbContext.on_key_press(key, modifiers)

    def update(self, dt):
        self._fbContext.update(dt)
