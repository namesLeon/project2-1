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



#include "Shader.hpp"
#include <glad/glad.h>
#include <glm/gtc/type_ptr.hpp>
#include <fstream>
#include <sstream>
#include <iostream>

// Utility: read entire file into string
static std::string readFile(const std::string& path) {
    std::ifstream ifs(path, std::ios::binary);
    if (!ifs) {
        throw std::runtime_error("Failed to open file: " + path);
    }
    std::ostringstream ss;
    ss << ifs.rdbuf();
    return ss.str();
}

Shader::~Shader() {
    if (program_ != 0) {
        glDeleteProgram(program_);
    }
}

// 🔹 Implementation of the helper
void Shader::checkShaderCompile(unsigned int shader, const std::string& name) {
    GLint success;
    glGetShaderiv(shader, GL_COMPILE_STATUS, &success);
    if (!success) {
        char log[512];
        glGetShaderInfoLog(shader, 512, nullptr, log);
        std::cerr << "Shader compile error in " << name << ":\n" << log << std::endl;
    } else {
        std::cout << "Compiled " << name << " successfully.\n";
    }
}

bool Shader::loadFromFiles(const std::string& vertPath, const std::string& fragPath) {
    std::string vertSrc = readFile(vertPath);
    std::string fragSrc = readFile(fragPath);

    std::cout << "Loaded vertex shader: " << vertPath << " (" << vertSrc.size() << " bytes)\n";
    std::cout << "Loaded fragment shader: " << fragPath << " (" << fragSrc.size() << " bytes)\n";

    const char* vsrc = vertSrc.c_str();
    const char* fsrc = fragSrc.c_str();

    // Vertex shader
    GLuint vs = glCreateShader(GL_VERTEX_SHADER);
    glShaderSource(vs, 1, &vsrc, nullptr);
    glCompileShader(vs);
    checkShaderCompile(vs, vertPath);

    // Fragment shader
    GLuint fs = glCreateShader(GL_FRAGMENT_SHADER);
    glShaderSource(fs, 1, &fsrc, nullptr);
    glCompileShader(fs);
    checkShaderCompile(fs, fragPath);

    // Link program
    program_ = glCreateProgram();
    glAttachShader(program_, vs);
    glAttachShader(program_, fs);
    glLinkProgram(program_);

    glDeleteShader(vs);
    glDeleteShader(fs);

    GLint success;
    glGetProgramiv(program_, GL_LINK_STATUS, &success);
    if (!success) {
        char log[512];
        glGetProgramInfoLog(program_, 512, nullptr, log);
        std::cerr << "Shader link error:\n" << log << std::endl;
        return false;
    } else {
        std::cout << "Shader program linked successfully.\n";
    }

    return true;
}

void Shader::use() const { glUseProgram(program_); }

void Shader::setFloat(const std::string& name, float v) const {
    int loc = glGetUniformLocation(program_, name.c_str());
    if (loc != -1) glUniform1f(loc, v);
}
void Shader::setVec2(const std::string& name, const glm::vec2& v) const {
    int loc = glGetUniformLocation(program_, name.c_str());
    if (loc != -1) glUniform2fv(loc, 1, &v.x);
}
void Shader::setVec3(const std::string& name, const glm::vec3& v) const {
    int loc = glGetUniformLocation(program_, name.c_str());
    if (loc != -1) glUniform3fv(loc, 1, &v.x);
}
void Shader::setVec4(const std::string& name, const glm::vec4& v) const {
    int loc = glGetUniformLocation(program_, name.c_str());
    if (loc != -1) glUniform4fv(loc, 1, &v.x);
}
void Shader::setInt(const std::string& name, int v) const {
    int loc = glGetUniformLocation(program_, name.c_str());
    if (loc != -1) glUniform1i(loc, v);
}
