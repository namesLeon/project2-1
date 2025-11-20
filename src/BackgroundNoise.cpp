// #define WIN32_LEAN_AND_MEAN
// #define NOMINMAX
// #include <windows.h>
// #include <mmsystem.h>
// #pragma comment(lib, "winmm.lib")

// #include <thread>
// #include <atomic>
// #include <chrono>
// #include <cmath>
// #include <iostream>
// #include <string>

// class BackgroundNoise {
// public:
//     BackgroundNoise(const std::string& musicPath, const std::string& cityPath)
//         : musicPath(musicPath), cityPath(cityPath) {}

//     void start() {
//         if (running) return;
//         running = true;
//         // Start two parallel audio threads
//         musicThread = std::thread(&BackgroundNoise::playMusic, this);
//         cityThread = std::thread(&BackgroundNoise::playCity, this);
//         volumeThread = std::thread(&BackgroundNoise::oscillateVolume, this);
//     }

//     void stop() {
//         running = false;
//         if (musicThread.joinable()) musicThread.join();
//         if (cityThread.joinable()) cityThread.join();
//         if (volumeThread.joinable()) volumeThread.join();
//         // Stop all sounds
//         PlaySound(nullptr, nullptr, 0);
//     }

// private:
//     std::string musicPath;
//     std::string cityPath;
//     std::atomic<bool> running{false};
//     std::thread musicThread;
//     std::thread cityThread;
//     std::thread volumeThread;

//     void playMusic() {
//         // Play soft classical music in loop
//         PlaySoundA(musicPath.c_str(), NULL, SND_FILENAME | SND_ASYNC | SND_LOOP);
//         while (running) {
//             std::this_thread::sleep_for(std::chrono::seconds(1));
//         }
//     }

//     void playCity() {
//         // Start city sounds loop
//         PlaySoundA(cityPath.c_str(), NULL, SND_FILENAME | SND_ASYNC | SND_LOOP);
//         while (running) {
//             std::this_thread::sleep_for(std::chrono::seconds(1));
//         }
//     }

//     void oscillateVolume() {
//         auto start = std::chrono::steady_clock::now();
//         while (running) {
//             auto now = std::chrono::steady_clock::now();
//             float t = std::chrono::duration<float>(now - start).count();

//             // Oscillate between 0.3 and 1.0 volume for city sounds
//             float mod = (std::sin(t * 0.5f) + 1.0f) * 0.5f; // 0–1
//             float cityVol = 0.3f + 0.7f * mod;
//             DWORD vol = static_cast<DWORD>(cityVol * 0xFFFF);
//             waveOutSetVolume(0, (vol << 16) | vol);

//             std::this_thread::sleep_for(std::chrono::milliseconds(200));
//         }
//     }
// };
