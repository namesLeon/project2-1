cmake_minimum_required(VERSION 3.15)
project(GIFWA LANGUAGES C CXX)

# ====== General C++ setup ======
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# ====== Detect and display vcpkg toolchain ======
if(DEFINED CMAKE_TOOLCHAIN_FILE)
    message(STATUS "Using toolchain: ${CMAKE_TOOLCHAIN_FILE}")
endif()

# ====== Source files ======
set(SOURCES
    src/main.cpp
    src/glad.c
    src/gl_utils.cpp
    src/Shader.cpp
    src/renderer.cpp
    src/stb_impl.cpp
    src/BackgroundNoise.cpp
)

add_executable(GIFWA ${SOURCES})

# ====== Include directories (common) ======
target_include_directories(GIFWA PRIVATE
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/include/glad
    ${CMAKE_SOURCE_DIR}/include/GLFW
    ${CMAKE_SOURCE_DIR}/include/glm
    ${CMAKE_SOURCE_DIR}/include/headers
    ${CMAKE_SOURCE_DIR}/maps
    ${CMAKE_SOURCE_DIR}/shaders
    ${CMAKE_SOURCE_DIR}/sounds
    ${CMAKE_SOURCE_DIR}/vcpkg/src
)

# ====== Platform-specific setup ======

# ---------- WINDOWS ----------
if(WIN32)
    message(STATUS "Configuring for Windows")

    include_directories(
        ${CMAKE_SOURCE_DIR}/vcpkg/installed/x64-windows-static/include
    )
    link_directories(${CMAKE_SOURCE_DIR}/vcpkg/installed/x64-windows-static/lib)

    target_link_libraries(GIFWA
        ${CMAKE_SOURCE_DIR}/lib/libglfw3dll.a
        opengl32
        gdi32
        ws2_32
        wsock32
    )

# ---------- LINUX ----------
elseif(UNIX AND NOT APPLE)
    message(STATUS "Configuring for Linux")

    find_package(OpenGL REQUIRED)
    find_package(glfw3 REQUIRED)
    find_package(PkgConfig REQUIRED)

    # Keep OpenAL via pkg-config; FFmpeg removed
    pkg_check_modules(OPENAL REQUIRED IMPORTED_TARGET openal)

    target_link_libraries(GIFWA
        OpenGL::GL
        glfw
        PkgConfig::OPENAL
        dl
        pthread
    )

# ---------- MACOS ----------
elseif(APPLE)
    message(STATUS "Configuring for macOS")

    find_package(OpenGL REQUIRED)
    find_package(glfw3 REQUIRED)
    find_library(COCOA_LIBRARY Cocoa)
    find_library(IOKIT_LIBRARY IOKit)
    find_library(COREVIDEO_LIBRARY CoreVideo)
    find_library(OPENAL_LIBRARY OpenAL)

    # FFmpeg find_* and include dirs REMOVED

    target_link_libraries(GIFWA
        glfw
        ${OPENGL_LIBRARIES}
        ${COCOA_LIBRARY}
        ${IOKIT_LIBRARY}
        ${COREVIDEO_LIBRARY}
        ${OPENAL_LIBRARY}
    )
endif()
