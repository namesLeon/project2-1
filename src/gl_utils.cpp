#define NOMINMAX
#define WIN32_LEAN_AND_MEAN
#include <windows.h>

#include <iostream>
#include <cmath>
#include <chrono>
#include <thread>
#include <ctime>
#include <algorithm> // for std::clamp
#include <vector>
#include <mutex>

// OpenAL and FFmpeg
#include <AL/al.h>
#include <AL/alc.h>
extern "C" {
#include <libavcodec/avcodec.h>
#include <libavformat/avformat.h>
#include <libswresample/swresample.h>
}


#include "gl_utils.hpp"
#include <glad/glad.h>
#include <GLFW/glfw3.h>
#include <iostream>


GLFWwindow* initWindow(const AppConfig& cfg) {
if (!glfwInit()) { std::cerr << "Failed to init GLFW\n"; return nullptr; }


#if defined(__APPLE__)
glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE);
glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
#else
glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
#endif


GLFWwindow* window = glfwCreateWindow(cfg.width, cfg.height, cfg.title.c_str(), nullptr, nullptr);
if (!window) { std::cerr << "Failed to create window\n"; glfwTerminate(); return nullptr; }


glfwMakeContextCurrent(window);
if (cfg.vsync) glfwSwapInterval(1);


if (!gladLoadGLLoader((GLADloadproc)glfwGetProcAddress)) {
std::cerr << "Failed to init GLAD\n";
return nullptr;
}


return window;
}


void pollEyeInput(EyeInput& eye) {
// TODO: Replace with your eye-tracker SDK call; keep values normalized in [0,1]
// Here we just keep the last value (no-op). You can also map mouse to gaze for testing.
}