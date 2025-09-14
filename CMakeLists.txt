cmake_minimum_required(VERSION 3.10)
project(GIFWA LANGUAGES C CXX)

# Stel C++ standaard in
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Include directories
include_directories(
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/include/glad
    ${CMAKE_SOURCE_DIR}/include/GLFW
    ${CMAKE_SOURCE_DIR}/include/glm
    ${CMAKE_SOURCE_DIR}/include/headers
)

# Voeg Client.cpp toe aan je bronbestanden
set(SOURCES
    src/main.cpp
    src/Client.cpp
    src/glad.c
    

)

# Maak executable
add_executable(GIFWA ${SOURCES})

# Voor Windows: link tegen de precompiled GLFW library
if(WIN32)
    # Link tegen de precompiled library in je lib folder
    target_link_libraries(GIFWA 
        ${CMAKE_SOURCE_DIR}/lib/libglfw3dll.a
        opengl32 
        gdi32
        ws2_32  # Winsock library toegevoegd aan GIFWA target
        wsock32 # Extra Winsock library (soms nodig)
    )
    
    # Kopieer de DLL naar de build folder
add_custom_command(TARGET GIFWA POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy
    ${CMAKE_SOURCE_DIR}/glfw3.dll
    $<TARGET_FILE_DIR:GIFWA>
)
endif()

# Voor Linux
if(UNIX AND NOT APPLE)
    find_package(OpenGL REQUIRED)
    find_package(glfw3 REQUIRED)
    target_link_libraries(GIFWA GL dl glfw)
endif()

# Voor macOS
if(APPLE)
    find_package(OpenGL REQUIRED)
    find_package(glfw3 REQUIRED)
    find_library(COCOA_LIBRARY Cocoa)
    find_library(IOKIT_LIBRARY IOKit)
    find_library(COREVIDEO_LIBRARY CoreVideo)
    target_link_libraries(GIFWA 
        glfw
        ${OPENGL_LIBRARIES}
        ${COCOA_LIBRARY}
        ${IOKIT_LIBRARY}
        ${COREVIDEO_LIBRARY}
    )
endif()