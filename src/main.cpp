
#include <algorithm>
#include <chrono>
#include <cmath>
#include <iostream>
#include <mutex>
#include <thread>
#include <vector>

#include <glad/glad.h>
#include <GLFW/glfw3.h>
#include <glm/glm.hpp>

#include "stb_image.h"
#include "gl_utils.hpp"   // initWindow, pollEyeInput (bool), EyeInput, AppConfig
#include "Shader.hpp"
#include "renderer.hpp"
// #include "BackgroundNoise.cpp"

// ------------------------------------
// Texture loading
// ------------------------------------
unsigned int loadTexture(const std::string& path) {
    int w, h, nrChannels;
    stbi_set_flip_vertically_on_load(true);
    unsigned char* data = stbi_load(path.c_str(), &w, &h, &nrChannels, 0);
    if (!data) {
        std::cerr << "[ERROR] Failed to load texture: " << path << std::endl;
        return 0;
    }
    GLenum format = (nrChannels == 1) ? GL_RED
                  : (nrChannels == 3) ? GL_RGB
                  : GL_RGBA;
    unsigned int texID;
    glGenTextures(1, &texID);
    glBindTexture(GL_TEXTURE_2D, texID);
    glTexImage2D(GL_TEXTURE_2D, 0, format, w, h, 0, format, GL_UNSIGNED_BYTE, data);
    glGenerateMipmap(GL_TEXTURE_2D);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    stbi_image_free(data);
    return texID;
}

// ------------------------------------
// Helper: get framebuffer resolution
// ------------------------------------
static glm::vec2 getResolution(GLFWwindow* win) {
    int w, h;
    glfwGetFramebufferSize(win, &w, &h);
    return glm::vec2((float)w, (float)h);
}

// ------------------------------------
// Main
// ------------------------------------
int main() {
    AppConfig cfg;
    cfg.width  = 1280;
    cfg.height = 720;
    cfg.title  = "Venice City - Eye Tracking Demo";
    cfg.vsync  = true;

    GLFWwindow* window = initWindow(cfg);
    if (!window) {
        std::cerr << "[ERROR] Failed to initialize window.\n";
        return -1;
    }

    Shader shader;
    if (!shader.loadFromFiles("../Shaders/quad.vert", "../Shaders/retrocity.frag")) {
        std::cerr << "[ERROR] Failed to load shaders.\n";
        return -2;
    }

    unsigned int texStone = loadTexture("../maps/Stone.jpg");
    unsigned int texWood  = loadTexture("../maps/WoodFloor.jpg");

    shader.use();
    shader.setInt("uChannel0", 0);
    shader.setInt("uChannel3", 1);

    Renderer renderer;
    renderer.init();
    renderer.setTextures(texStone, texWood);

    auto t0 = std::chrono::steady_clock::now();

    EyeInput eye;  // hasData defaults to false now
    bool useMouse = false;                 // start in FILE gaze mode
    int  prevBtnState = GLFW_RELEASE;
    double lastClickTime = 0.0;
    const double dblClickWindow = 0.30;    // seconds
    static bool everHadEyeData = false;    // persists across frames

    // BackgroundNoise bg("../../sounds/venice_music.wav", "../../sounds/city_sounds.wav");
    // bg.start();

    while (!glfwWindowShouldClose(window)) {
        glfwPollEvents();

        // ---- Double-click toggle (LMB) ----
        int btn = glfwGetMouseButton(window, GLFW_MOUSE_BUTTON_LEFT);
        double nowSecs = glfwGetTime();
        if (btn == GLFW_PRESS && prevBtnState == GLFW_RELEASE) {
            if (nowSecs - lastClickTime <= dblClickWindow) {
                useMouse = !useMouse;
                std::cout << "[INPUT] Switched to " << (useMouse ? "MOUSE" : "GAZE_FILE") << "\n";
                lastClickTime = 0.0;
            } else {
                lastClickTime = nowSecs;
            }
        }
        prevBtnState = btn;

        glm::vec2 res = getResolution(window);

        // 1) Try to refresh from file. If a NEW sample arrived, this returns true.
        bool gotNew = pollEyeInput(eye);
        if (gotNew) {
            everHadEyeData = true;
        }

        // 2) If toggled to mouse, override gaze continuously
        if (useMouse) {
            double mx, my;
            glfwGetCursorPos(window, &mx, &my);
            eye.gaze = glm::vec2((float)mx / res.x, 1.0f - (float)my / res.y);
            everHadEyeData = true; // mouse provides data
        }

        // Report hasData based on whether we've ever had valid gaze
        eye.hasData = everHadEyeData;

        // Time
        auto now = std::chrono::steady_clock::now();
        float t = std::chrono::duration<float>(now - t0).count();

        // ---- Update shader uniforms ----
        shader.use();
        shader.setFloat("uTime", t);
        shader.setVec2("uResolution", res);
        shader.setInt("uHasEye", eye.hasData ? 1 : 0);
        shader.setVec2("uEyeGaze", eye.gaze);

       
        double mx, my;
        glfwGetCursorPos(window, &mx, &my);
        glm::vec4 mouseUniform((float)mx, (float)my,
        glfwGetMouseButton(window, GLFW_MOUSE_BUTTON_LEFT) == GLFW_PRESS ? 1.0f : 0.0f, 0.0f);
        shader.setVec4("uMouse", mouseUniform);

        // ---- Render ----
        renderer.draw(window, shader, t, res, eye);
        glfwSwapBuffers(window);
    }

    // bg.stop();
    glfwTerminate();
    return 0;
}
