#include "gl_utils.hpp"
#include "Shader.hpp"
#include "renderer.hpp"
#include "stb_image.h"


#include <glad/glad.h>
#include <GLFW/glfw3.h>
#include <glm/glm.hpp>
#include <chrono>
#include <iostream>


unsigned int loadTexture(const std::string& path) {
    int w, h, nrChannels;
    stbi_set_flip_vertically_on_load(true); 
    unsigned char* data = stbi_load(path.c_str(), &w, &h, &nrChannels, 0);
    if (!data) {
        std::cerr << "[ERROR] Failed to load texture: " << path << std::endl;
        return 0;
    }

    GLenum format = (nrChannels == 1) ? GL_RED :
                    (nrChannels == 3) ? GL_RGB : GL_RGBA;

    unsigned int texID;
    glGenTextures(1, &texID);
    glBindTexture(GL_TEXTURE_2D, texID);
    glTexImage2D(GL_TEXTURE_2D, 0, format, w, h, 0, format, GL_UNSIGNED_BYTE, data);
    glGenerateMipmap(GL_TEXTURE_2D);

    // Filtering/wrapping
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);

    stbi_image_free(data);
    return texID;
}

// Helper: get framebuffer resolution
static glm::vec2 getResolution(GLFWwindow* win) {
    int w, h;
    glfwGetFramebufferSize(win, &w, &h);
    return glm::vec2((float)w, (float)h);
}

int main() {
    AppConfig cfg;
    cfg.width = 1280;
    cfg.height = 720;
    cfg.title = "Venice City - Eye Tracking Demo";
    cfg.vsync = true;

    GLFWwindow* window = initWindow(cfg);
    if (!window) {
        std::cerr << "[ERROR] Failed to initialize window.\n";
        return -1;
    }

    Shader shader;
    if (!shader.loadFromFiles("../../Shaders/quad.vert", "../../Shaders/retrocity.frag")) {
        std::cerr << "[ERROR] Failed to load shaders.\n";
        return -2;
    }
    unsigned int texStone   = loadTexture("../../maps/Stone.jpg");
unsigned int texWood    = loadTexture("../../maps/WoodFloor.jpg");

// Bind sampler2D uniforms naar texture units
shader.use();
shader.setInt("uChannel0", 0); // Stone → unit 0
shader.setInt("uChannel3", 1); // Wood → unit 1

    Renderer renderer;
    renderer.init();
    renderer.setTextures(texStone, texWood);
    auto t0 = std::chrono::steady_clock::now();

    EyeInput eye; // default stays centered until SDK integration

    // ==== MAIN LOOP ====
    while (!glfwWindowShouldClose(window)) {
        glfwPollEvents();

        // Simulate eye gaze using mouse (for testing)
        double mx, my;
        glfwGetCursorPos(window, &mx, &my);
        glm::vec2 res = getResolution(window);
        eye.gaze = glm::vec2((float)mx / res.x, 1.0f - (float)my / res.y);
        eye.hasData = true;

        pollEyeInput(eye); // Replace with real SDK later

        auto now = std::chrono::steady_clock::now();
        float t = std::chrono::duration<float>(now - t0).count();

        // === Update shader uniforms ===
        shader.use();
        shader.setFloat("uTime", t);
        shader.setVec2("uResolution", res);
        shader.setInt("uHasEye", eye.hasData ? 1 : 0);
        shader.setVec2("uEyeGaze", eye.gaze);

        // optional: feed mouse to uMouse if you want Shadertoy-like controls
        glm::vec4 mouseUniform(mx, my, glfwGetMouseButton(window, GLFW_MOUSE_BUTTON_LEFT) == GLFW_PRESS ? 1.0f : 0.0f, 0.0f);
        shader.setVec4("uMouse", mouseUniform);

        // === Render ===
        renderer.draw(window, shader, t, res, eye);

        glfwSwapBuffers(window);
    }

    glfwTerminate();
    return 0;
}
