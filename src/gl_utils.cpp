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
#include <filesystem>
#include <fstream>
#include <regex>
#include <string>
#include <sstream>



#include "gl_utils.hpp"
#include <glad/glad.h>
#include <GLFW/glfw3.h>
#include <iostream>

struct EyeInput {
    float x = 0.5f;
    float y = 0.5f;
    bool ok = false;
};

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


static inline float clamp01(float v) {
    return std::clamp(v, 0.0f, 1.0f);
}


void pollEyeInput(EyeInput& eye, const std::string& path = "gaze_out.txt")
{
    static std::filesystem::file_time_type lastWrite{};
    std::error_code ec;

    if (!std::filesystem::exists(path, ec)) {
        return;
    }

    auto nowWrite = std::filesystem::last_write_time(path, ec);
    if (ec || (lastWrite == nowWrite)) {
        return;
    }

    std::ifstream in(path);
    if (!in) return;

    std::string line;
    std::getline(in, line);
    in.close();

    std::regex re_xy(R"(x\s*:\s*([0-9]*\.?[0-9]+)\s*y\s*:\s*([0-9]*\.?[0-9]+))",
                     std::regex::icase);
    std::smatch m;

    double x = 0.5, y = 0.5;
    bool parsed = false;

    if (std::regex_search(line, m, re_xy) && m.size() >= 3) {
        x = std::stod(m[1].str());
        y = std::stod(m[2].str());
        parsed = true;
    } else {
        std::istringstream iss(line);
        if (iss >> x >> y) {
            parsed = true;
        }
    }

    if (parsed) {
        eye.x = clamp01(static_cast<float>(x));
        eye.y = clamp01(static_cast<float>(y));
        eye.ok = true;
        lastWrite = nowWrite; 
    }
}