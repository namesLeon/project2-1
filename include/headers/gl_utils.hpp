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
    // Normalized gaze in [0,1]x[0,1]; (0,0) = bottom-left
    glm::vec2 gaze = glm::vec2(0.5f, 0.5f);
    // True once we've ever received valid gaze (from file or mouse)
    bool hasData = false;
};

// Initialize window & GL context
GLFWwindow* initWindow(const AppConfig& cfg);

// Poll gaze file. Returns true ONLY if a NEW sample was parsed this call.
// If it returns true, 'eye.gaze' is updated to the new value.
bool pollEyeInput(EyeInput& eye);
