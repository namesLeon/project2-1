#pragma once
#include <glm/glm.hpp>
class Shader;
struct GLFWwindow;
struct EyeInput;


class Renderer {
public:
Renderer();
~Renderer();


bool init();
void draw(GLFWwindow* window, Shader& shader, float timeSec, const glm::vec2& resolution, const EyeInput& eye);


private:
unsigned int vao_ = 0, vbo_ = 0;
};