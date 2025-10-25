#pragma once
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX

#include <windows.h>
#include <string>
#include <thread>
#include <atomic>
#include <mutex>

class BackgroundNoise {
public:
    BackgroundNoise(const std::string& musicPath, const std::string& cityPath);
    ~BackgroundNoise();

    void start();
    void stop();

private:
    void playAudio();
    void playMusic();
    void playCity();

    std::string musicPath;
    std::string cityPath;

    std::atomic<bool> running{false};
    std::thread audioThread;
    std::thread musicThread;
    std::thread cityThread;
    std::mutex volumeMutex;
};
