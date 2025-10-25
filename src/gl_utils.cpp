#include "gl_utils.hpp"

#include <glad/glad.h>
#include <GLFW/glfw3.h>

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <regex>
#include <sstream>
#include <system_error>
#include <string>

// ------------------------------------
// helpers
// ------------------------------------
static inline float clamp01(float v) { return std::clamp(v, 0.0f, 1.0f); }

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

    glViewport(0, 0, cfg.width, cfg.height);
    return window;
}

// ------------------------------------
// gaze file path resolution (search up a few dirs)
// ------------------------------------
static std::filesystem::path resolveGazePath() {
    std::filesystem::path cur = std::filesystem::current_path();
    for (int i = 0; i < 6; ++i) { // try ., .., ../.., ...
        auto candidate = cur / "gaze_out.txt";
        std::error_code ec;
        if (std::filesystem::exists(candidate, ec) && !ec) {
            return candidate;
        }
        cur = cur.parent_path();
    }
    return {};
}

// ------------------------------------
// eye polling (reads last non-empty line if file changed)
// Returns true iff a NEW sample was parsed this call
// ------------------------------------
bool pollEyeInput(EyeInput& eye) {
    static std::filesystem::path gazePath = resolveGazePath();
    static std::filesystem::file_time_type lastWrite{};

    if (gazePath.empty()) {
        // Try again lazily in case cwd changed
        gazePath = resolveGazePath();
        if (gazePath.empty()) {
            // Uncomment if you want spammy logs:
            // std::cerr << "[EYE] Could not locate gaze_out.txt. cwd=" << std::filesystem::current_path() << "\n";
            return false;
        }
    }

    std::error_code ec;
    if (!std::filesystem::exists(gazePath, ec)) {
        // std::cerr << "[EYE] Gaze file not found at: " << gazePath << "\n";
        return false;
    }

    auto nowWrite = std::filesystem::last_write_time(gazePath, ec);
    if (ec || nowWrite == lastWrite) {
        return false; // unchanged or error
    }

    std::ifstream in(gazePath);
    if (!in) {
        std::cerr << "[EYE] Failed to open: " << gazePath << "\n";
        return false;
    }

    // Read the LAST non-empty line (generator appends lines)
    std::string line, lastLine;
    while (std::getline(in, line)) {
        if (!line.empty()) lastLine = line;
    }

    // Formats supported:
    //   "x:<num> y:<num>"
    //   "<x> <y>"
    std::regex re_xy(R"(x\s*:\s*([0-9]*\.?[0-9]+)\s*y\s*:\s*([0-9]*\.?[0-9]+))", std::regex::icase);
    std::smatch m;

    double x = 0.5, y = 0.5;
    bool parsed = false;
    if (std::regex_search(lastLine, m, re_xy) && m.size() >= 3) {
        x = std::stod(m[1].str());
        y = std::stod(m[2].str());
        parsed = true;
    } else {
        std::istringstream iss(lastLine);
        if (iss >> x >> y) {
            parsed = true;
        }
    }

    if (!parsed) return false;

    eye.gaze.x = clamp01(static_cast<float>(x));
    eye.gaze.y = clamp01(static_cast<float>(y));
    lastWrite = nowWrite;

    
    std::cout << "[EYE] Parsed gaze = x:" << eye.gaze.x
              << " y:" << eye.gaze.y << "  (" << gazePath.string() << ")\n";

    return true; 
}
