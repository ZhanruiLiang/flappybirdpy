# version 330 core
in float alphaOut;
in vec2 texcoord;
out vec4 fragColor;

uniform sampler2D textureSampler;

void main() {
    fragColor = texture(textureSampler, texcoord) * vec4(1, 1, 1, alphaOut);
}
