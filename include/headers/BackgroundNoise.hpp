#pragma once
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX

#include <windows.h> // needed by OpenAL on Windows
#include <ctime>  
#include <string>
#include <thread>
#include <atomic>
#include <vector>
#include <mutex>
#include <AL/al.h>
#include <AL/alc.h>

class BackgroundNoise {
public:
    BackgroundNoise(const std::string& musicPath, const std::string& cityPath);
    ~BackgroundNoise();

    void start();
    void stop();

    // Optional manual volume control
    void setCityVolume(float volume);
    void setMusicVolume(float volume);

private:
    void audioThreadFunc();
    void updateCityVolume(float time);

    bool loadAudioFile(const std::string& path, ALuint& buffer, ALenum& format, ALsizei& freq);

private:
    std::thread audioThread;
    std::atomic<bool> running{false};

    ALCdevice* device = nullptr;
    ALCcontext* context = nullptr;

    ALuint sourceMusic = 0;
    ALuint sourceCity = 0;

    ALuint bufferMusic = 0;
    ALuint bufferCity = 0;

    float cityVolume = 1.0f;
    float musicVolume = 0.4f;
    std::mutex volumeMutex;
};
