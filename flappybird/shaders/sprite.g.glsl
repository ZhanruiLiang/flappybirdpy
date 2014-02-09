# version 330 core
layout (points) in;
layout (triangle_strip, max_vertices=4) out;

const int N = 30;
uniform vec4 boxes[N];
uniform sampler2D textureSampler;
uniform vec2 screenSize;

in vec2 pos[];
in float alpha[];
in float angle[];
in int textureId[];

out vec2 texcoord;
out float alphaOut;

const mat4 M1 = mat4(1, 1, 0, 0,  0, 0, 0, 0,  0, 0, 1, 1,  0, 0, 0, 0);
const mat4 M2 = mat4(0, 0, 0, 0,  1, 0, 1, 0,  0, 0, 0, 0,  0 ,1, 0, 1);

void main() {
    vec2 tSize = textureSize(textureSampler, 0);
    vec4 box = boxes[textureId[0]];
    vec4 X = M1 * box;
    vec4 Y = M2 * box;
    vec2 centerTexSpace = vec2((box[0] + box[2]) / 2, (box[1] + box[3]) / 2);
    float a = angle[0];
    mat2 rotation = mat2(cos(a), sin(a), -sin(a), cos(a));
    for(int i = 0; i < 4; i++) {
        vec2 posTexSpace = vec2(X[i], Y[i]);
        texcoord = vec2(posTexSpace.x / tSize.x, 1 - posTexSpace.y / tSize.y);
        alphaOut = alpha[0];
        vec2 posViewSpace = pos[0] + rotation * (posTexSpace - centerTexSpace);
        gl_Position = vec4(
            posViewSpace.x / screenSize.x * 2.010,
            posViewSpace.y / screenSize.y * 2.010,
            0, 1
        );
        EmitVertex();
    }
    EndPrimitive();
}
