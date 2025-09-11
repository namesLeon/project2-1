cmake_minimum_required(VERSION 3.10)
project(GIFWA LANGUAGES C CXX)

# Stel C++ standaard in
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Include directories
include_directories(
    include
    include/glad
)

# Zoek GLFW
find_package(glfw3 REQUIRED)

# Voor Windows: zoek OpenGL
if(WIN32)
    find_package(OpenGL REQUIRED)
endif()

# Bronbestanden
set(SOURCES
    src/main.cpp
    src/glad.c
)

# Maak executable
add_executable(GIFWA ${SOURCES})

# Link libraries
target_link_libraries(GIFWA
    glfw
    ${OPENGL_LIBRARIES}
)

# Windows specifieke instellingen
if(WIN32)
    target_link_libraries(GIFWA opengl32 gdi32)
endif()

# Linux specifieke instellingen
if(UNIX AND NOT APPLE)
    target_link_libraries(GIFWA GL dl)
endif()

# Mac specifieke instellingen
if(APPLE)
    find_library(COCOA_LIBRARY Cocoa)
    find_library(IOKIT_LIBRARY IOKit)
    find_library(COREVIDEO_LIBRARY CoreVideo)
    target_link_libraries(GIFWA 
        ${COCOA_LIBRARY}
        ${IOKIT_LIBRARY}
        ${COREVIDEO_LIBRARY}
    )
endif()