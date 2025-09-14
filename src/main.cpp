#define GLFW_INCLUDE_NONE 
#include <GLFW/glfw3.h>
#include <glad/glad.h>
#include <iostream>
#include <cmath>
#include <vector>
#include <random>
#include <algorithm>
#include <numeric>
#include <map>
#include "headers/Client.hpp"
// TO DO:  add MOREEEEEEEEEEE DOCUMENTATION AND REMOVE UNUSED CODE, AND CLEAN UP DUTCH COMMENTS FFS
#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <glm/gtc/type_ptr.hpp>
// TO DO: Split into multiple files, and try to fix the weird parallax effect
// TO DO: Add textures instead of colors
// TO DO: Add better world generation (maybe perlin noise?)

// Vertex shader source met lighting
// Vertex shader source
class PerlinNoise {
private:
    std::vector<int> permutation;
    
    double fade(double t) {
        return t * t * t * (t * (t * 6 - 15) + 10);
    }
    
    double lerp(double t, double a, double b) {
        return a + t * (b - a);
    }
    
    double grad(int hash, double x, double y, double z) {
        int h = hash & 15;
        double u = h < 8 ? x : y;
        double v = h < 4 ? y : h == 12 || h == 14 ? x : z;
        return ((h & 1) == 0 ? u : -u) + ((h & 2) == 0 ? v : -v);
    }
    
public:
    PerlinNoise(unsigned int seed = 0) {
        permutation.resize(256);
        std::iota(permutation.begin(), permutation.end(), 0);
        std::default_random_engine engine(seed);
        std::shuffle(permutation.begin(), permutation.end(), engine);
        permutation.insert(permutation.end(), permutation.begin(), permutation.end());
    }
    
    double noise(double x, double y, double z) {
        int X = (int)floor(x) & 255;
        int Y = (int)floor(y) & 255;
        int Z = (int)floor(z) & 255;
        
        x -= floor(x);
        y -= floor(y);
        z -= floor(z);
        
        double u = fade(x);
        double v = fade(y);
        double w = fade(z);
        
        int A = permutation[X] + Y;
        int AA = permutation[A] + Z;
        int AB = permutation[A + 1] + Z;
        int B = permutation[X + 1] + Y;
        int BA = permutation[B] + Z;
        int BB = permutation[B + 1] + Z;
        
        return lerp(w, lerp(v, lerp(u, grad(permutation[AA], x, y, z),
                                   grad(permutation[BA], x - 1, y, z)),
                           lerp(u, grad(permutation[AB], x, y - 1, z),
                                   grad(permutation[BB], x - 1, y - 1, z))),
                   lerp(v, lerp(u, grad(permutation[AA + 1], x, y, z - 1),
                                   grad(permutation[BA + 1], x - 1, y, z - 1)),
                           lerp(u, grad(permutation[AB + 1], x, y - 1, z - 1),
                                   grad(permutation[BB + 1], x - 1, y - 1, z - 1))));
    }
};

// Camera class for first-person movement
class Camera {
public:
    glm::vec3 position;
    glm::vec3 front;
    glm::vec3 up;
    glm::vec3 right;
    glm::vec3 worldUp;
    
    float yaw;
    float pitch;
    
    float movementSpeed;
    float mouseSensitivity;
    float zoom;
    
    Camera(glm::vec3 position = glm::vec3(0.0f, 0.0f, 0.0f), 
           glm::vec3 up = glm::vec3(0.0f, 1.0f, 0.0f), 
           float yaw = -90.0f, float pitch = 0.0f) 
        : front(glm::vec3(0.0f, 0.0f, -1.0f)), movementSpeed(5.0f), 
          mouseSensitivity(0.1f), zoom(45.0f) {
        this->position = position;
        this->worldUp = up;
        this->yaw = yaw;
        this->pitch = pitch;
        updateCameraVectors();
    }
    
    glm::mat4 getViewMatrix() {
        return glm::lookAt(position, position + front, up);
    }
    
    void processKeyboard(int direction, float deltaTime) {
        float velocity = movementSpeed * deltaTime;
        if (direction == 0) // Forward
            position += front * velocity;
        if (direction == 1) // Backward
            position -= front * velocity;
        if (direction == 2) // Left
            position -= right * velocity;
        if (direction == 3) // Right
            position += right * velocity;
        if(direction == 4) // Up
            position += worldUp * velocity;
        // Keep camera at ground level + eye height
        position.y = 5.7f; // Eye height
    }
    
    void processMouseMovement(float xoffset, float yoffset, GLboolean constrainPitch = true) {
        xoffset *= mouseSensitivity;
        yoffset *= mouseSensitivity;
        
        yaw += xoffset;
        pitch += yoffset;
        
        if (constrainPitch) {
            if (pitch > 89.0f)
                pitch = 89.0f;
            if (pitch < -89.0f)
                pitch = -89.0f;
        }
        
        updateCameraVectors();
    }
    
private:
    void updateCameraVectors() {
        glm::vec3 newFront;
        newFront.x = cos(glm::radians(yaw)) * cos(glm::radians(pitch));
        newFront.y = sin(glm::radians(pitch));
        newFront.z = sin(glm::radians(yaw)) * cos(glm::radians(pitch));
        front = glm::normalize(newFront);
        
        right = glm::normalize(glm::cross(front, worldUp));
        up = glm::normalize(glm::cross(right, front));
    }
};

// Vertex shader source
const char* vertexShaderSource = R"(
    #version 330 core
    layout (location = 0) in vec3 aPos;
    layout (location = 1) in vec3 aColor;
    
    out vec3 ourColor;
    
    uniform mat4 model;
    uniform mat4 view;
    uniform mat4 projection;
    uniform vec3 blockOffset;
    
    void main()
    {
        gl_Position = projection * view * model * vec4(aPos + blockOffset, 1.0);
        ourColor = aColor;
    }
)";

// Fragment shader source
const char* fragmentShaderSource = R"(
    #version 330 core
    in vec3 ourColor;
    out vec4 FragColor;
    
    void main()
    {
        FragColor = vec4(ourColor, 1.0);
    }
)";

// Function to generate a cube with colors
std::vector<float> generateCube(float size, glm::vec3 color) {
    float half = size / 2.0f;
    return {
        // Front face
        -half, -half,  half, color.r, color.g, color.b,
         half, -half,  half, color.r, color.g, color.b,
         half,  half,  half, color.r, color.g, color.b,
         half,  half,  half, color.r, color.g, color.b,
        -half,  half,  half, color.r, color.g, color.b,
        -half, -half,  half, color.r, color.g, color.b,
        
        // Back face
        -half, -half, -half, color.r*0.8f, color.g*0.8f, color.b*0.8f,
         half, -half, -half, color.r*0.8f, color.g*0.8f, color.b*0.8f,
         half,  half, -half, color.r*0.8f, color.g*0.8f, color.b*0.8f,
         half,  half, -half, color.r*0.8f, color.g*0.8f, color.b*0.8f,
        -half,  half, -half, color.r*0.8f, color.g*0.8f, color.b*0.8f,
        -half, -half, -half, color.r*0.8f, color.g*0.8f, color.b*0.8f,
        
        // Left face
        -half,  half,  half, color.r*0.9f, color.g*0.9f, color.b*0.9f,
        -half,  half, -half, color.r*0.9f, color.g*0.9f, color.b*0.9f,
        -half, -half, -half, color.r*0.9f, color.g*0.9f, color.b*0.9f,
        -half, -half, -half, color.r*0.9f, color.g*0.9f, color.b*0.9f,
        -half, -half,  half, color.r*0.9f, color.g*0.9f, color.b*0.9f,
        -half,  half,  half, color.r*0.9f, color.g*0.9f, color.b*0.9f,
        
        // Right face
         half,  half,  half, color.r*0.9f, color.g*0.9f, color.b*0.9f,
         half,  half, -half, color.r*0.9f, color.g*0.9f, color.b*0.9f,
         half, -half, -half, color.r*0.9f, color.g*0.9f, color.b*0.9f,
         half, -half, -half, color.r*0.9f, color.g*0.9f, color.b*0.9f,
         half, -half,  half, color.r*0.9f, color.g*0.9f, color.b*0.9f,
         half,  half,  half, color.r*0.9f, color.g*0.9f, color.b*0.9f,
        
        // Bottom face
        -half, -half, -half, color.r*0.7f, color.g*0.7f, color.b*0.7f,
         half, -half, -half, color.r*0.7f, color.g*0.7f, color.b*0.7f,
         half, -half,  half, color.r*0.7f, color.g*0.7f, color.b*0.7f,
         half, -half,  half, color.r*0.7f, color.g*0.7f, color.b*0.7f,
        -half, -half,  half, color.r*0.7f, color.g*0.7f, color.b*0.7f,
        -half, -half, -half, color.r*0.7f, color.g*0.7f, color.b*0.7f,
        
        // Top face
        -half,  half, -half, color.r, color.g, color.b,
         half,  half, -half, color.r, color.g, color.b,
         half,  half,  half, color.r, color.g, color.b,
         half,  half,  half, color.r, color.g, color.b,
        -half,  half,  half, color.r, color.g, color.b,
        -half,  half, -half, color.r, color.g, color.b
    };
}

// Simple procedural world generation with Perlin noise
std::vector<glm::vec3> generateWorld(int width, int depth, int maxHeight) {
    std::vector<glm::vec3> blocks;
    PerlinNoise perlin(12345); // Seed for consistent generation
    
    for (int x = -width/2; x < width/2; x++) {
        for (int z = -depth/2; z < depth/2; z++) {
            // Use Perlin noise for height
            double noiseValue = perlin.noise(x * 0.1, z * 0.1, 0.5);
            int height = static_cast<int>((noiseValue + 1.0) * 0.5 * maxHeight);
            
            if (height < 1) height = 1;
            if (height > maxHeight) height = maxHeight;
            
            // Add blocks from bottom to height
            for (int y = 0; y < height; y++) {
                blocks.push_back(glm::vec3(x, y, z));
            }
        }
    }
    
    return blocks;
}

// Function to check if a block is visible (simple frustum culling)
bool isBlockVisible(const glm::vec3& blockPos, const glm::vec3& cameraPos, const glm::vec3& cameraFront) {
    glm::vec3 toBlock = blockPos - cameraPos;
    float distance = glm::length(toBlock);
    
    // Only render blocks within a certain distance
    if (distance > 20.0f) return false;
    
    // Simple dot product test for front-facing blocks
    glm::vec3 dirToBlock = glm::normalize(toBlock);
    float dotProduct = glm::dot(cameraFront, dirToBlock);
    
    // Only render blocks in front of the camera
    return dotProduct > -0.5f; // Allow some leeway
}

// Mouse callback
void mouse_callback(GLFWwindow* window, double xpos, double ypos) {
    static bool firstMouse = true;
    static float lastX = 400, lastY = 300;
    
    if (firstMouse) {
        lastX = xpos;
        lastY = ypos;
        firstMouse = false;
    }
    
    float xoffset = xpos - lastX;
    float yoffset = lastY - ypos; // Reversed since y-coordinates go from bottom to top
    
    lastX = xpos;
    lastY = ypos;
    
    Camera* camera = static_cast<Camera*>(glfwGetWindowUserPointer(window));
    camera->processMouseMovement(xoffset, yoffset);
}

int main()
{
    std::cout << "Starting Minecraft-like World with First-Person Camera..." << std::endl;

    // Initialize GLFW
    if (!glfwInit()) {
        std::cout << "Failed to initialize GLFW" << std::endl;
        return -1;
    }

    // Configure GLFW
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);

    // Create window
    GLFWwindow* window = glfwCreateWindow(800, 600, "Minecraft-like World", NULL, NULL);

    if (!window) {
        std::cout << "Failed to create GLFW window" << std::endl;
        glfwTerminate();
        return -1;
    }
    glfwMakeContextCurrent(window);
    
    // Set input mode to capture mouse
    glfwSetInputMode(window, GLFW_CURSOR, GLFW_CURSOR_DISABLED);

    // Load OpenGL functions with Glad
    if (!gladLoadGLLoader((GLADloadproc)glfwGetProcAddress)) {
        std::cout << "Failed to initialize GLAD" << std::endl;
        return -1;
    }

    // Set viewport
    glViewport(0, 0, 800, 600);
    glEnable(GL_DEPTH_TEST);

    // Build and compile shaders
    unsigned int vertexShader = glCreateShader(GL_VERTEX_SHADER);
    glShaderSource(vertexShader, 1, &vertexShaderSource, NULL);
    glCompileShader(vertexShader);

    // Check for vertex shader compile errors
    int success;
    char infoLog[512];
    glGetShaderiv(vertexShader, GL_COMPILE_STATUS, &success);
    if (!success) {
        glGetShaderInfoLog(vertexShader, 512, NULL, infoLog);
        std::cout << "ERROR::SHADER::VERTEX::COMPILATION_FAILED\n" << infoLog << std::endl;
    }

    unsigned int fragmentShader = glCreateShader(GL_FRAGMENT_SHADER);
    glShaderSource(fragmentShader, 1, &fragmentShaderSource, NULL);
    glCompileShader(fragmentShader);

    // Check for fragment shader compile errors
    glGetShaderiv(fragmentShader, GL_COMPILE_STATUS, &success);
    if (!success) {
        glGetShaderInfoLog(fragmentShader, 512, NULL, infoLog);
        std::cout << "ERROR::SHADER::FRAGMENT::COMPILATION_FAILED\n" << infoLog << std::endl;
    }

    unsigned int shaderProgram = glCreateProgram();
    glAttachShader(shaderProgram, vertexShader);
    glAttachShader(shaderProgram, fragmentShader);
    glLinkProgram(shaderProgram);

    // Check for linking errors
    glGetProgramiv(shaderProgram, GL_LINK_STATUS, &success);
    if (!success) {
        glGetProgramInfoLog(shaderProgram, 512, NULL, infoLog);
        std::cout << "ERROR::SHADER::PROGRAM::LINKING_FAILED\n" << infoLog << std::endl;
    }

    glDeleteShader(vertexShader);
    glDeleteShader(fragmentShader);

    // Generate cube vertices with different colors for different block types
    std::vector<float> grassCube = generateCube(1.0f, glm::vec3(0.0f, 0.8f, 0.0f));
    std::vector<float> dirtCube = generateCube(1.0f, glm::vec3(0.5f, 0.3f, 0.1f));
    std::vector<float> stoneCube = generateCube(1.0f, glm::vec3(0.5f, 0.5f, 0.5f));

    // Setup VAO, VBO for each block type
    unsigned int VAOs[3], VBOs[3];
    glGenVertexArrays(3, VAOs);
    glGenBuffers(3, VBOs);
    
    // Grass VAO
    glBindVertexArray(VAOs[0]);
    glBindBuffer(GL_ARRAY_BUFFER, VBOs[0]);
    glBufferData(GL_ARRAY_BUFFER, grassCube.size() * sizeof(float), grassCube.data(), GL_STATIC_DRAW);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 6 * sizeof(float), (void*)0);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 6 * sizeof(float), (void*)(3 * sizeof(float)));
    glEnableVertexAttribArray(1);
    
    // Dirt VAO
    glBindVertexArray(VAOs[1]);
    glBindBuffer(GL_ARRAY_BUFFER, VBOs[1]);
    glBufferData(GL_ARRAY_BUFFER, dirtCube.size() * sizeof(float), dirtCube.data(), GL_STATIC_DRAW);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 6 * sizeof(float), (void*)0);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 6 * sizeof(float), (void*)(3 * sizeof(float)));
    glEnableVertexAttribArray(1);
    
    // Stone VAO
    glBindVertexArray(VAOs[2]);
    glBindBuffer(GL_ARRAY_BUFFER, VBOs[2]);
    glBufferData(GL_ARRAY_BUFFER, stoneCube.size() * sizeof(float), stoneCube.data(), GL_STATIC_DRAW);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 6 * sizeof(float), (void*)0);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 6 * sizeof(float), (void*)(3 * sizeof(float)));
    glEnableVertexAttribArray(1);
    
    // Unbind VAO
    glBindVertexArray(0);

    // Generate world
    std::vector<glm::vec3> worldBlocks = generateWorld(64, 64, 8);

    // Create camera
    Camera camera(glm::vec3(0.0f, 1.7f, 3.0f));
    glfwSetWindowUserPointer(window, &camera);
    glfwSetCursorPosCallback(window, mouse_callback);

    // Timing variables
    float deltaTime = 0.0f;
    float lastFrame = 0.0f;

    // Main render loop
    while (!glfwWindowShouldClose(window)) {
        // Calculate delta time
        float currentFrame = glfwGetTime();
        deltaTime = currentFrame - lastFrame;
        lastFrame = currentFrame;

        // Process input
        if (glfwGetKey(window, GLFW_KEY_ESCAPE) == GLFW_PRESS)
            glfwSetWindowShouldClose(window, true);
        
        if (glfwGetKey(window, GLFW_KEY_W) == GLFW_PRESS)
            camera.processKeyboard(0, deltaTime);
        if (glfwGetKey(window, GLFW_KEY_S) == GLFW_PRESS)
            camera.processKeyboard(1, deltaTime);
        if (glfwGetKey(window, GLFW_KEY_A) == GLFW_PRESS)
            camera.processKeyboard(2, deltaTime);
        if (glfwGetKey(window, GLFW_KEY_D) == GLFW_PRESS)
            camera.processKeyboard(3, deltaTime);
        if(glfwGetKey(window, GLFW_KEY_SPACE) == GLFW_PRESS)
            camera.processKeyboard(4, deltaTime); 

        // Clear screen
        glClearColor(0.53f, 0.81f, 0.98f, 1.0f); // Sky blue
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

        // Use shader program
        glUseProgram(shaderProgram);

        // Set up projection matrix
        glm::mat4 projection = glm::perspective(glm::radians(45.0f), 800.0f / 600.0f, 0.1f, 100.0f);
        glUniformMatrix4fv(glGetUniformLocation(shaderProgram, "projection"), 1, GL_FALSE, glm::value_ptr(projection));

        // Set up view matrix
        glm::mat4 view = camera.getViewMatrix();
        glUniformMatrix4fv(glGetUniformLocation(shaderProgram, "view"), 1, GL_FALSE, glm::value_ptr(view));

        // Set up model matrix (identity matrix since we're using blockOffset)
        glm::mat4 model = glm::mat4(1.0f);
        glUniformMatrix4fv(glGetUniformLocation(shaderProgram, "model"), 1, GL_FALSE, glm::value_ptr(model));

        // Render blocks
        int renderedBlocks = 0;
        for (const auto& blockPos : worldBlocks) {
            if (isBlockVisible(blockPos, camera.position, camera.front)) {
                // Determine block type based on height
                int blockType;
                if (blockPos.y == 0) {
                    blockType = 2; // Stone at bottom
                } else if (blockPos.y < 3) {
                    blockType = 1; // Dirt in middle layers
                } else {
                    blockType = 0; // Grass on top
                }

                // Set block offset uniform
                glUniform3f(glGetUniformLocation(shaderProgram, "blockOffset"), 
                           blockPos.x, blockPos.y, blockPos.z);

                // Draw the block
                glBindVertexArray(VAOs[blockType]);
                glDrawArrays(GL_TRIANGLES, 0, 90);
                renderedBlocks++;
            }
        }

        // Swap buffers and poll events
        glfwSwapBuffers(window);
        glfwPollEvents();
    }

    // Cleanup
    glDeleteVertexArrays(3, VAOs);
    glDeleteBuffers(3, VBOs);
    glDeleteProgram(shaderProgram);
    run();
    glfwTerminate();
    return 0;
}