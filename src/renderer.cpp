#include "renderer.hpp"
#include "Shader.hpp"
#include "gl_utils.hpp"
#include <glad/glad.h>
#include <GLFW/glfw3.h>


Renderer::Renderer() {}
Renderer::~Renderer(){ if(vbo_) glDeleteBuffers(1,&vbo_); if(vao_) glDeleteVertexArrays(1,&vao_); }


bool Renderer::init(){
// Fullscreen quad covering NDC [-1,1]
float quad[] = {
-1.f,-1.f, 1.f,-1.f, 1.f, 1.f,
-1.f,-1.f, 1.f, 1.f, -1.f, 1.f
};
glGenVertexArrays(1,&vao_); glBindVertexArray(vao_);
glGenBuffers(1,&vbo_); glBindBuffer(GL_ARRAY_BUFFER, vbo_);
glBufferData(GL_ARRAY_BUFFER, sizeof(quad), quad, GL_STATIC_DRAW);
glEnableVertexAttribArray(0);
glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2*sizeof(float), (void*)0);
glBindVertexArray(0);
return true;
}


void Renderer::draw(GLFWwindow* window, Shader& shader, float timeSec, const glm::vec2& resolution, const EyeInput& eye){
int w, h; glfwGetFramebufferSize(window, &w, &h);
glViewport(0,0,w,h);
glClearColor(0.02f,0.02f,0.03f,1.0f);
glClear(GL_COLOR_BUFFER_BIT);


shader.use();
shader.setVec2("iResolution", resolution);
shader.setFloat("iTime", timeSec);
shader.setVec2("uEyeGaze", eye.gaze);
shader.setInt("uHasEye", eye.hasData ? 1 : 0);


glBindVertexArray(vao_);
glDrawArrays(GL_TRIANGLES, 0, 6);
glBindVertexArray(0);
}