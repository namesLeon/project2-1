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


#include "renderer.hpp"
#include "Shader.hpp"
#include "gl_utils.hpp"
#include <glad/glad.h>
#include <GLFW/glfw3.h>
#include "stb_image.h"


Renderer::Renderer() {}
Renderer::~Renderer() {
    if (vbo_) glDeleteBuffers(1, &vbo_);
    if (vao_) glDeleteVertexArrays(1, &vao_);
}

bool Renderer::init() {
    // Fullscreen quad covering NDC [-1,1]
    float quad[] = {
        -1.f, -1.f,
         1.f, -1.f,
         1.f,  1.f,
        -1.f, -1.f,
         1.f,  1.f,
        -1.f,  1.f
    };

    glGenVertexArrays(1, &vao_);
    glBindVertexArray(vao_);

    glGenBuffers(1, &vbo_);
    glBindBuffer(GL_ARRAY_BUFFER, vbo_);
    glBufferData(GL_ARRAY_BUFFER, sizeof(quad), quad, GL_STATIC_DRAW);

    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * sizeof(float), (void*)0);

    glBindVertexArray(0);
    return true;
}

void Renderer::draw(GLFWwindow* window, Shader& shader, float timeSec, const glm::vec2& resolution, const EyeInput& eye) {
    int w, h;
    glfwGetFramebufferSize(window, &w, &h);
    glViewport(0, 0, w, h);

    glClearColor(0.02f, 0.02f, 0.03f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT);

    shader.use();

    // ===== Update uniforms consistent with venice_opengl_frag.glsl =====
    shader.setFloat("uTime", timeSec);
    shader.setVec2("uResolution", resolution);
    shader.setVec2("uEyeGaze", eye.gaze);
    shader.setInt("uHasEye", eye.hasData ? 1 : 0);

    // Optional: simulate Shadertoy-like uMouse using GLFW cursor
    double mx, my;
    glfwGetCursorPos(window, &mx, &my);
    float pressed = (glfwGetMouseButton(window, GLFW_MOUSE_BUTTON_LEFT) == GLFW_PRESS) ? 1.0f : 0.0f;
    shader.setVec4("uMouse", glm::vec4((float)mx, (float)my, pressed, 0.0f));

    // ===== Draw fullscreen quad =====
    glBindVertexArray(vao_);
    glActiveTexture(GL_TEXTURE0);
    glBindTexture(GL_TEXTURE_2D, texStone_);

    glActiveTexture(GL_TEXTURE1);
    glBindTexture(GL_TEXTURE_2D, texWood_);
    glDrawArrays(GL_TRIANGLES, 0, 6);
    glBindVertexArray(0);
}
