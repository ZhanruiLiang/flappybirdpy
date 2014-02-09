from .sprites import Sprite, html_color

class Button(Sprite):
    maskColor = None
    size = (0, 0)

    def on_click(self):
        pass

    def _on_click(self):
        self.fade_out(on_finish=self.mark_to_remove)
        self.on_click()

    def in_rect(self, xy):
        w, h = self.size
        cx, cy = self.screenPos
        w /= 2
        h /= 2
        return cx - w <= xy[0] < cx + w and cy - h <= xy[1] < cy + h

class StartButton(Button):
    maskColor = html_color('e86100')
    size = (44, 16)
    initScreenPos = (-40, -40)

class ScoreButton(Button):
    maskColor = html_color('e86101')
    initScreenPos = (40, -40)

class GetReady(Sprite):
    maskColor = (0, 0, 0)
