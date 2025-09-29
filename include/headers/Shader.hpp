#pragma once
#include <string>
#include <glm/glm.hpp>

class Shader {
public:
    Shader() : program_(0) {}
    ~Shader();

    bool loadFromFiles(const std::string& vertPath, const std::string& fragPath);

    void use() const;

    void setFloat(const std::string& name, float v) const;
    void setVec2(const std::string& name, const glm::vec2& v) const;
    void setVec3(const std::string& name, const glm::vec3& v) const;
    void setInt(const std::string& name, int v) const;

private:
    unsigned int program_;

    static void checkShaderCompile(unsigned int shader, const std::string& name);
};
