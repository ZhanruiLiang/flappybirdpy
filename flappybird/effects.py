class Effect:
    sprite = None
    finished = False
    time = 0

    def __init__(self, sprite):
        self.sprite = sprite

    def update(self, dt):
        self.time += dt


class FadeOut(Effect):
    endTime = 0.2

    def __init__(self, sprite, on_finish):
        super().__init__(sprite)
        self.update(0)
        self._on_finish = on_finish

    def update(self, dt):
        if self.finished:
            return
        self.time += dt
        self.sprite.alpha = 1 - self.time / self.endTime
        if self.time >= self.endTime:
            if self._on_finish:
                self._on_finish()
            self.finished = True
