import random
import pyglet
from . import sprites
from .bird import Bird
from . import ui
from . import config


class GameState:
    ready = 'ready'
    entering = 'entering'
    flyying = 'flyying'
    falling = 'falling'
    showboard = 'showboard'


class Context:
    sprites = []

    def __init__(self, app):
        self.app = app

    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)

    def update(self, dt):
        for sprite in self.sprites:
            sprite.update(dt)
        self.sprites = [sp for sp in self.sprites if not sp._needRemove]
        # print(self, self.sprites)

    def on_mouse_press(self, x, y, button, modifiers):
        pass

    def on_key_press(self, key, modifiers):
        pass

    def switch_to_context(self, contextClass):
        self.app.set_context(contextClass)


class Splash(Context):
    pass


class Menu(Context):
    def __init__(self, app):
        super().__init__(app)

        startButton = ui.StartButton()
        startButton.on_click = self.start

        scoreButton = ui.ScoreButton()
        scoreButton.on_click = self.show_score

        background = sprites.Background()

        self.sprites = [background, startButton, scoreButton]

    def start(self):
        self.switch_to_context(Game)

    def show_score(self):
        self.switch_to_context(ScoreBoard)


class ScoreBoard(Context):
    pass


class Game(Context):
    def __init__(self, app):
        super().__init__(app)
        self.state = GameState.ready
        self.bird = Bird()
        self.upperPillars = [sprites.UpperPillar() for _ in range(config.nPillars)]
        self.lowerPillars = [sprites.LowerPillar() for _ in range(config.nPillars)]
        self.put_pillars()
        background = sprites.Background()
        self.floor = sprites.Floor()
        self.tapToStart = tapToStart = sprites.TapToStart()
        tapToStart.on_click = self.start
        self.sprites = [background] + self.upperPillars + self.lowerPillars\
            + [self.bird, self.floor, tapToStart]
        self._viewX = 0
        self.score = 0

    def start(self):
        self.state = GameState.entering
        self.tapToStart.fade_out(self.tapToStart.mark_to_remove)
        self.bird.started = True
        self.bird.flap()

    def get_notch_offset(self):
        return random.randint(*config.notchCenterRange)

    def put_pillars(self):
        for i in range(config.nPillars):
            pillar = self.upperPillars[i]
            pillar1 = self.lowerPillars[i]
            pillar.x = pillar1.x = config.beginDistance + i * config.gapWidth
            pillar.offset = pillar1.offset = self.get_notch_offset()

    def hit(self):
        self.floor.moving = False
        self.bird.on_hit()

    def add_score(self):
        self.score += 1

    def update(self, dt):
        for i in range(config.nPillars):
            pillar = self.upperPillars[i]
            pillar1 = self.lowerPillars[i]
            if pillar.x + config.pillarWidth / 2 - self._viewX\
                    + config.screenWidth / 2 < 0:
                pillar1.x = pillar.x = pillar.x + config.gapWidth * config.nPillars
                pillar1.offset = pillar.offset = self.get_notch_offset()
            pillar.screenPos = \
                (pillar.x - self._viewX, pillar.initY + pillar.offset)
            pillar1.screenPos = \
                (pillar1.x - self._viewX, pillar1.initY + pillar1.offset)

        if self.state in (GameState.entering, GameState.flyying):
            self._viewX += config.scrollDistancePerFrame

        super().update(dt)

    def on_key_press(self, key, modifiers):
        if key == pyglet.window.key.SPACE:
            self.on_tap()

    def on_mouse_press(self, x, y, button, modifiers):
        self.on_tap()

    def on_tap(self):
        if self.state == GameState.ready:
            self.start()
        elif self.state in (GameState.entering, GameState.flyying):
            self.bird.flap()
