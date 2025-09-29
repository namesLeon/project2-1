#include "gl_utils.hpp"
#include "Shader.hpp"
#include "renderer.hpp"

#include <glad/glad.h>
#include <GLFW/glfw3.h>
#include <glm/glm.hpp>
#include <chrono>
#include <iostream>

static glm::vec2 getResolution(GLFWwindow* win) {
    int w, h;
    glfwGetFramebufferSize(win, &w, &h);
    return glm::vec2((float)w, (float)h);
}

int main() {
    std::cout << "[DEBUG] Starting program...\n";

    AppConfig cfg;
    cfg.width = 1280;
    cfg.height = 720;
    cfg.title = "Retro City (OpenGL)";
    cfg.vsync = true;

    std::cout << "[DEBUG] Initializing window...\n";
    GLFWwindow* window = initWindow(cfg);
    if (!window) {
        std::cerr << "[ERROR] Failed to initialize window.\n";
        return -1;
    }
    std::cout << "[DEBUG] Window created successfully.\n";

    std::cout << "[DEBUG] Loading shaders...\n";
    Shader shader;
    try {
        if (!shader.loadFromFiles("../../Shaders/quad.vert", "../../Shaders/retrocity.frag")) {
            std::cerr << "[ERROR] Shader load failed (returned false).\n";
            return -2;
        }
    } catch (const std::exception& e) {
        std::cerr << "[EXCEPTION] " << e.what() << std::endl;
        return -3;
    }
    std::cout << "[DEBUG] Shaders loaded successfully.\n";

    std::cout << "[DEBUG] Initializing renderer...\n";
    Renderer renderer;
    renderer.init();
    std::cout << "[DEBUG] Renderer initialized successfully.\n";

    auto t0 = std::chrono::steady_clock::now();
    EyeInput eye; // default stays centered until you integrate SDK
    std::cout << "[DEBUG] EyeInput created.\n";

    std::cout << "[DEBUG] Entering main loop...\n";
    while (!glfwWindowShouldClose(window)) {
        glfwPollEvents();
        std::cout << "[DEBUG] LOOP TICK\n";

        // Optional: map mouse to eye gaze for testing
        double mx, my;
        glfwGetCursorPos(window, &mx, &my);
        glm::vec2 res = getResolution(window);
        eye.gaze = glm::vec2((float)mx / res.x, 1.0f - (float)my / res.y);
        eye.hasData = true;

        std::cout << "[DEBUG] Eye gaze: (" << eye.gaze.x << ", " << eye.gaze.y << ")\n";

        pollEyeInput(eye); // replace with real SDK
        std::cout << "[DEBUG] pollEyeInput done.\n";

        auto now = std::chrono::steady_clock::now();
        float t = std::chrono::duration<float>(now - t0).count();
        std::cout << "[DEBUG] Time since start: " << t << "s\n";

        // 🔹 Bind shader + update uniforms here
        shader.use();
        shader.setFloat("iTime", t);
        shader.setVec2("iResolution", res);
        shader.setInt("uHasEye", eye.hasData ? 1 : 0);
        shader.setVec2("uEyeGaze", eye.gaze);
        std::cout << "[DEBUG] Shader uniforms updated.\n";

        std::cout << "[DEBUG] Calling renderer.draw...\n";
        renderer.draw(window, shader, t, res, eye);
        std::cout << "[DEBUG] renderer.draw completed.\n";

        glfwSwapBuffers(window);
        std::cout << "[DEBUG] Buffers swapped.\n";
    }

    std::cout << "[DEBUG] Exiting loop, terminating GLFW...\n";
    glfwTerminate();
    std::cout << "[DEBUG] Program finished.\n";
    return 0;
}
