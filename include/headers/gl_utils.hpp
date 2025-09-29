#pragma once
#include <string>
#include <glm/vec2.hpp>
#include <glm/vec3.hpp>


struct GLFWwindow;


struct AppConfig {
int width = 1280;
int height = 720;
std::string title = "Retro City";
bool vsync = true;
};


struct EyeInput {
// Normalized gaze in [0,1]x[0,1] screen space; (0,0) = bottom-left
glm::vec2 gaze = glm::vec2(0.5f, 0.5f);
bool hasData = false;
};


GLFWwindow* initWindow(const AppConfig& cfg);
void pollEyeInput(EyeInput& eye); // placeholder hook; integrate your SDK inside