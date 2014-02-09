# version 330 core

in vec4 sprite;
in float alphaIn;

out vec2 pos;
out float alpha;
out float angle;
out int textureId;

void main() {
    pos = sprite.xy;
    angle = sprite.z;
    textureId = int(sprite.w + .5);
    alpha = alphaIn;
}
