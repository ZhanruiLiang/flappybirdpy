from contextlib import contextmanager
from OpenGL.GL import *

__all__ = [
    'compile_shader', 'report_limits', 'AttributeNotFoundError',
    'UniformNotFoundError', 'VertexBuffer', 'IndexBuffer', 'Program',
    'Texture2D', 'TextureUnit', 'VertexBufferSlot'
]


def compile_shader(source, shaderType):
    """
    source: str source code
    shaderType: GL_VERTEX_SHADER, GL_FRAGMENT_SHADER or GL_GEOMETRY_SHADER
    """
    shader = glCreateShader(shaderType)
    glShaderSource(shader, source)
    glCompileShader(shader)
    result = glGetShaderiv(shader, GL_COMPILE_STATUS)
    info = glGetShaderInfoLog(shader).decode('utf-8')
    if info:
        print('Shader compilation info:\n{}'.format(info))
    if result == GL_FALSE:
        raise Exception('GLSL compile error: {}'.format(shaderType))
    return shader

class AttributeNotFoundError(Exception):
    pass

class UniformNotFoundError(Exception):
    pass

class GLResource:
    def __init__(self):
        self._id = None

    @property
    def glId(self):
        if self._id is None:
            self._id = self.allocate()
        return self._id

    def allocate(self):
        "Allocate GL resource and return a id. "
        raise NotImplementedError()

    def dealloc(self):
        raise NotImplementedError()

    def free(self):
        if self._id is None:
            return
        self.dealloc()
        self._id = None

    def __del__(self):
        if self._id is not None:
            print(self, 'has not been freed')


class Texture2D(GLResource):
    MAG_FILTER = GL_LINEAR
    MIN_FILTER = GL_LINEAR_MIPMAP_LINEAR

    def __init__(self, image):
        GLResource.__init__(self)
        self.image = image

    def allocate(self):
        textureId = self.make_texture(self.image)
        del self.image
        glBindTexture(GL_TEXTURE_2D, textureId)
        self.configure()
        return textureId

    def configure(self):
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, self.MAG_FILTER)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, self.MIN_FILTER)
        glGenerateMipmap(GL_TEXTURE_2D)

    def dealloc(self):
        glDeleteTextures([self.glId])

    @staticmethod
    def make_texture(image):
        data = image.convert('RGBA').tobytes()
        width, height = image.size
        glEnable(GL_TEXTURE_2D)
        textureId = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, textureId)
        assert textureId > 0, 'Fail to get new texture id.'
        glTexImage2D(
            GL_TEXTURE_2D, 0,
            GL_RGBA,  # internal format
            width, height,
            0,  # border, must be 0
            GL_RGBA,  # input data format
            GL_UNSIGNED_BYTE,
            data,
        )
        return textureId


class VertexBuffer(GLResource):
    target = GL_ARRAY_BUFFER

    def __init__(self, data, usage_hint=GL_STATIC_DRAW):
        """
        :param numpy.ndarray data: Data that to be put into buffer
        :param GLenum usage_hint: The last parameter of glBufferData
        """
        self.usageHint = usage_hint
        self._length = len(data)
        self.data = data
        GLResource.__init__(self)

    def allocate(self):
        id = glGenBuffers(1)
        data = self.data
        del self.data
        glBindBuffer(self.target, id)
        glBufferData(self.target, data, self.usageHint)
        return id

    def dealloc(self):
        glDeleteBuffers(1, [self.glId])

    def __len__(self):
        return self._length


class IndexBuffer(VertexBuffer):
    target = GL_ELEMENT_ARRAY_BUFFER


class VertexBufferSlot:
    def __init__(self, location, item_size, data_type):
        self.location = location
        self.itemSize = item_size
        self.dataType = data_type

    def set_buffer(self, buffer):
        glBindBuffer(GL_ARRAY_BUFFER, buffer.glId)
        glVertexAttribPointer(
            self.location, self.itemSize, self.dataType, GL_FALSE, 0, None)


class Program(GLResource):
    def __init__(self, shaderDatas, bufs):
        """
        shaderDatas: A list of (filename, shaderType) tuples.
        bufs: A list of (attributeName, size, typeEnum) tuples.
        """
        GLResource.__init__(self)
        self._alocs = {}  # Attribute locations buffer
        self._ulocs = {}  # Uniform locations buffer
        self.bufs = bufs
        self.shaderDatas = shaderDatas

    def allocate(self):
        self.id = id = glCreateProgram()
        shaders = []
        try:
            for name, type in self.shaderDatas:
                with open(name, 'r') as infile:
                    source = infile.read()
                shader = compile_shader(source, type)
                glAttachShader(id, shader)
                shaders.append(shader)
            glLinkProgram(id)
        finally:
            for shader in shaders:
                glDeleteShader(shader)

        assert self.check_linked()
        assert self.check_valid()

        # Make VAO
        self._buffers = {}
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        # Make buffer slots
        for name, size, type in self.bufs:
            loc = glGetAttribLocation(id, name.encode('ascii'))
            if loc < 0:
                raise AttributeNotFoundError(name)
            self._buffers[name] = VertexBufferSlot(loc, size, type)

        glUseProgram(0)
        del self.bufs, self.shaderDatas
        return self.id

    def dealloc(self):
        glDeleteVertexArrays(1, [self.vao])
        glDeleteProgram(self.glId)
        del self.id

    def set_buffer(self, name, data):
        self._buffers[name].set_buffer(data)

    @contextmanager
    def batch_draw(self):
        self.use()
        glBindVertexArray(self.vao)
        self.enable_attribs()
        self.prepare_draw()
        yield
        self.post_draw()
        self.disable_attribs()
        self.unuse()

    def prepare_draw(self):
        pass

    def post_draw(self):
        pass

    def enable_attribs(self):
        for buf in self._buffers.values():
            glEnableVertexAttribArray(buf.location)

    def disable_attribs(self):
        for buf in self._buffers.values():
            glDisableVertexAttribArray(buf.location)

    def draw(self, primitive_type, count):
        glDrawArrays(primitive_type, 0, count)

    def get_uniform_loc(self, name):
        if name not in self._ulocs:
            loc = glGetUniformLocation(self.glId, name.encode('ascii'))
            if loc < 0:
                raise UniformNotFoundError(name)
            self._ulocs[name] = loc
        else:
            loc = self._ulocs[name]
        return loc

    def get_attrib_loc(self, name):
        if name not in self._alocs:
            loc = glGetAttribLocation(self.glId, name.encode('ascii'))
            if loc < 0:
                raise AttributeNotFoundError(name)
            self._alocs[name] = loc
        else:
            loc = self._alocs[name]
        return loc

    def print_info(self):
        info = glGetProgramInfoLog(self.id).decode('ascii')
        if info:
            print('Program info log:', info)

    def check_valid(self):
        glValidateProgram(self.id)
        result = glGetProgramiv(self.id, GL_VALIDATE_STATUS)
        if result == GL_FALSE:
            self.print_info()
            return False
        return True

    def check_linked(self):
        result = glGetProgramiv(self.id, GL_LINK_STATUS)
        if result == GL_FALSE:
            self.print_info()
            return False
        return True

    def use(self):
        glUseProgram(self.glId)

    def unuse(self):
        glUseProgram(0)

    def set_matrix(self, name, mat):
        glUniformMatrix4fv(self.get_uniform_loc(name), 1, GL_TRUE, mat)


class TextureUnit:
    def __init__(self, id):
        self.id = id
        self.glenum = globals()['GL_TEXTURE' + str(id)]


def report_limits():
    names = [
        GL_MAX_VERTEX_UNIFORM_BLOCKS, GL_MAX_GEOMETRY_UNIFORM_BLOCKS,
        GL_MAX_FRAGMENT_UNIFORM_BLOCKS, GL_MAX_TEXTURE_UNITS,
    ]
    for name in names:
        print(repr(name), glGetIntegerv(name))
