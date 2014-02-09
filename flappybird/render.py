import Image
import os
import numpy as np

from . import gllib as gl
from . import config


def get_resource_path(*subPath):
    return os.path.join(os.path.dirname(__file__), *subPath)


class ArrayBuffer(gl.GLResource):
    def __init__(self, usageHint):
        super().__init__()
        self.usageHint = usageHint

    def allocate(self):
        id = gl.glGenBuffers(1)
        return id

    def dealloc(self):
        gl.glDeleteBuffers(1, [self.glId])

    def set_data(self, data):
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.glId)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, data, self.usageHint)


class Texture(gl.Texture2D):
    MAG_FILTER = gl.GL_NEAREST
    MIN_FILTER = gl.GL_NEAREST

    def __init__(self):
        image = Image.open(get_resource_path('images', 'texture.png'))
        super().__init__(image)


class Render(gl.Program):
    def __init__(self):
        super().__init__([
            (get_resource_path('shaders', 'sprite.v.glsl'), gl.GL_VERTEX_SHADER),
            (get_resource_path('shaders', 'sprite.g.glsl'), gl.GL_GEOMETRY_SHADER),
            (get_resource_path('shaders', 'sprite.f.glsl'), gl.GL_FRAGMENT_SHADER),
        ], [
            ('sprite', 4, gl.GL_FLOAT),
            ('alphaIn', 1, gl.GL_FLOAT),
        ])
        self._screenSize = config.screenWidth, config.screenHeight
        self._make_boxes()
        self._arrayBuffers = [
            ArrayBuffer(gl.GL_DYNAMIC_DRAW), ArrayBuffer(gl.GL_DYNAMIC_DRAW)]
        self.texture = Texture()
        self.textureUnit = gl.TextureUnit(0)

    def _make_boxes(self):
        image = Image.open(get_resource_path('images', 'spritemask.png'))
        data = image.load()
        w, h = image.size
        boxes = {}
        for x in range(w):
            for y in range(h):
                color = data[x, y]
                if color[3] == 0:
                    continue
                color = color[:3]
                pixel = (x, h - y)
                if color not in boxes:
                    boxes[color] = [pixel]
                else:
                    boxes[color].append(pixel)
        id = 0
        boxesArray = np.zeros((len(boxes), 4), dtype=gl.GLfloat)
        colorToId = {}
        for color, pixels in boxes.items():
            xs = [x for x, _ in pixels]
            ys = [y for _, y in pixels]
            boxesArray[id] = (min(xs), min(ys), max(xs) + 0, max(ys) + 0)
            colorToId[color] = id
            id += 1
        self._boxesArray = boxesArray
        self._maskColorToId = colorToId
        self._textureSize = (w, h)

    def free(self):
        for buf in self._arrayBuffers:
            buf.free()

    def draw_sprites(self, sprites):
        """
        Draw sprites in given order
        """
        spriteBuf, alphaBuf = self._arrayBuffers
        sprites = [sp for sp in sprites if sp.maskColor]

        spriteBufData = np.zeros((len(sprites), 4), dtype=gl.GLfloat)
        for i, sp in enumerate(sprites):
            spriteBufData[i, 0:2] = sp.screenPos
            spriteBufData[i, 2] = sp.angle
            spriteBufData[i, 3] = self._maskColorToId[sp.maskColor]
            # print(sp, self._boxesArray[self._maskColorToId[sp.maskColor]])
        spriteBuf.set_data(spriteBufData)

        alphaBufData = np.array([sp.alpha for sp in sprites], dtype=gl.GLfloat)
        alphaBuf.set_data(alphaBufData)
        # Setup buffers
        self.set_buffer('sprite', spriteBuf)
        self.set_buffer('alphaIn', alphaBuf)
        # Setup uniforms
        gl.glUniform4fv(
            self.get_uniform_loc('boxes'), len(self._boxesArray), self._boxesArray)
        gl.glUniform2fv(
            self.get_uniform_loc('screenSize'), 1, self._screenSize)
        # Setup texture
        gl.glActiveTexture(self.textureUnit.glenum)
        gl.glUniform1i(self.get_uniform_loc('textureSampler'), self.textureUnit.id)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture.glId)
        # Draw
        self.draw(gl.GL_POINTS, len(sprites))
