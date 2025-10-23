#include "gl_utils.hpp"  // must be first so EyeInput/AppConfig are complete

#include <glad/glad.h>
#include <GLFW/glfw3.h>

#include <algorithm>     // std::clamp
#include <filesystem>
#include <fstream>
#include <iostream>
#include <regex>
#include <sstream>
#include <system_error>

// ------------------------------------
// helpers
// ------------------------------------
static inline float clamp01(float v) {
    return std::clamp(v, 0.0f, 1.0f);
}

// ------------------------------------
// window init
// ------------------------------------
GLFWwindow* initWindow(const AppConfig& cfg) {
    if (!glfwInit()) {
        std::cerr << "[ERROR] Failed to init GLFW\n";
        return nullptr;
    }

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
    if (!window) {
        std::cerr << "[ERROR] Failed to create GLFW window\n";
        glfwTerminate();
        return nullptr;
    }

    glfwMakeContextCurrent(window);
    glfwSwapInterval(cfg.vsync ? 1 : 0);

    if (!gladLoadGLLoader((GLADloadproc)glfwGetProcAddress)) {
        std::cerr << "[ERROR] Failed to initialize GLAD\n";
        glfwDestroyWindow(window);
        glfwTerminate();
        return nullptr;
    }

    // Initial viewport
    glViewport(0, 0, cfg.width, cfg.height);

    return window;
}

// ------------------------------------
// eye polling (reads "gaze_out.txt" if updated)
// ------------------------------------
void pollEyeInput(EyeInput& eye) {
    static std::filesystem::file_time_type lastWrite{};
    static const std::string path = "gaze_out.txt";

    std::error_code ec;
    if (!std::filesystem::exists(path, ec)) {
        return; // no file yet
    }

    auto nowWrite = std::filesystem::last_write_time(path, ec);
    if (ec || (lastWrite == nowWrite)) {
        return; // unchanged or error querying time
    }

    std::ifstream in(path);
    if (!in) return;

    std::string line;
    std::getline(in, line);

    // Formats supported:
    //   "x: <num> y: <num>"
    //   "<x> <y>"
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
        eye.gaze.x = clamp01(static_cast<float>(x));
        eye.gaze.y = clamp01(static_cast<float>(y));
        eye.hasData = true;
        lastWrite = nowWrite;
    }
}
