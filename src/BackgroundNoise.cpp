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


static bool decodeToPCM(const std::string& path, std::vector<int16_t>& pcmOut, int& sampleRate, int& channels) {
    AVFormatContext* fmt = nullptr;
    if (avformat_open_input(&fmt, path.c_str(), nullptr, nullptr) < 0) return false;
    if (avformat_find_stream_info(fmt, nullptr) < 0) return false;

    int audioStreamIndex = av_find_best_stream(fmt, AVMEDIA_TYPE_AUDIO, -1, -1, nullptr, 0);
    if (audioStreamIndex < 0) return false;

    AVCodecParameters* codecPar = fmt->streams[audioStreamIndex]->codecpar;
    const AVCodec* codec = avcodec_find_decoder(codecPar->codec_id);
    if (!codec) return false;

    AVCodecContext* ctx = avcodec_alloc_context3(codec);
    avcodec_parameters_to_context(ctx, codecPar);
    if (avcodec_open2(ctx, codec, nullptr) < 0) return false;

    SwrContext* swr = swr_alloc_set_opts(
        nullptr,
        AV_CH_LAYOUT_STEREO, AV_SAMPLE_FMT_S16, ctx->sample_rate,
        av_get_default_channel_layout(ctx->channels), ctx->sample_fmt, ctx->sample_rate,
        0, nullptr);
    swr_init(swr);

    AVPacket* pkt = av_packet_alloc();
    AVFrame* frame = av_frame_alloc();

    std::vector<int16_t> output;
    while (av_read_frame(fmt, pkt) >= 0) {
        if (pkt->stream_index == audioStreamIndex) {
            if (avcodec_send_packet(ctx, pkt) == 0) {
                while (avcodec_receive_frame(ctx, frame) == 0) {
                    uint8_t* outData[2];
                    int outSamples = swr_get_out_samples(swr, frame->nb_samples);
                    std::vector<int16_t> buffer(outSamples * 2);
                    outData[0] = (uint8_t*)buffer.data();
                    int converted = swr_convert(swr, outData, outSamples,
                        (const uint8_t**)frame->data, frame->nb_samples);
                    output.insert(output.end(), buffer.begin(), buffer.begin() + converted * 2);
                }
            }
        }
        av_packet_unref(pkt);
    }

    pcmOut = std::move(output);
    sampleRate = ctx->sample_rate;
    channels = 2;

    av_frame_free(&frame);
    av_packet_free(&pkt);
    swr_free(&swr);
    avcodec_free_context(&ctx);
    avformat_close_input(&fmt);
    return true;
}

bool BackgroundNoise::loadAudioFile(const std::string& path, ALuint& buffer, ALenum& format, ALsizei& freq) {
    std::vector<int16_t> pcm;
    int sampleRate = 0, channels = 0;
    if (!decodeToPCM(path, pcm, sampleRate, channels)) {
        std::cerr << "Failed to load audio: " << path << std::endl;
        return false;
    }

    format = (channels == 1) ? AL_FORMAT_MONO16 : AL_FORMAT_STEREO16;
    freq = sampleRate;

    alGenBuffers(1, &buffer);
    alBufferData(buffer, format, pcm.data(), pcm.size() * sizeof(int16_t), freq);
    return true;
}

BackgroundNoise::BackgroundNoise(const std::string& musicPath, const std::string& cityPath) {
    device = alcOpenDevice(nullptr);
    if (!device) {
        std::cerr << "[AUDIO] Failed to open audio device\n";
        return;
    }
    context = alcCreateContext(device, nullptr);
    alcMakeContextCurrent(context);

    alGenSources(1, &sourceMusic);
    alGenSources(1, &sourceCity);

    ALenum format;
    ALsizei freq;
    if (loadAudioFile(musicPath, bufferMusic, format, freq)) {
        alSourcei(sourceMusic, AL_BUFFER, bufferMusic);
        alSourcei(sourceMusic, AL_LOOPING, AL_TRUE);
        alSourcef(sourceMusic, AL_GAIN, musicVolume);
    }

    if (loadAudioFile(cityPath, bufferCity, format, freq)) {
        alSourcei(sourceCity, AL_BUFFER, bufferCity);
        alSourcei(sourceCity, AL_LOOPING, AL_TRUE);
        alSourcef(sourceCity, AL_GAIN, cityVolume);
    }
}

BackgroundNoise::~BackgroundNoise() {
    stop();

    alDeleteSources(1, &sourceMusic);
    alDeleteSources(1, &sourceCity);
    alDeleteBuffers(1, &bufferMusic);
    alDeleteBuffers(1, &bufferCity);
    alcDestroyContext(context);
    alcCloseDevice(device);
}

void BackgroundNoise::start() {
    if (running) return;
    running = true;
    alSourcePlay(sourceMusic);
    alSourcePlay(sourceCity);
    audioThread = std::thread(&BackgroundNoise::audioThreadFunc, this);
}

void BackgroundNoise::stop() {
    if (!running) return;
    running = false;
    if (audioThread.joinable()) audioThread.join();
    alSourceStop(sourceMusic);
    alSourceStop(sourceCity);
}

void BackgroundNoise::setCityVolume(float volume) {
    std::lock_guard<std::mutex> lock(volumeMutex);
    cityVolume = std::clamp(volume, 0.0f, 1.0f);
}

void BackgroundNoise::setMusicVolume(float volume) {
    std::lock_guard<std::mutex> lock(volumeMutex);
    musicVolume = std::clamp(volume, 0.0f, 1.0f);
}

void BackgroundNoise::audioThreadFunc() {
    using clock = std::chrono::steady_clock;
    auto start = clock::now();
    while (running) {
        auto now = clock::now();
        float t = std::chrono::duration<float>(now - start).count();
        updateCityVolume(t);
        std::this_thread::sleep_for(std::chrono::milliseconds(200));
    }
}

void BackgroundNoise::updateCityVolume(float time) {
    std::lock_guard<std::mutex> lock(volumeMutex);
    float mod = (std::sin(time * 0.3f) + 1.0f) * 0.5f; // oscillates between 0–1
    float newVolume = 0.2f + 0.8f * mod;              // range 0.2–1.0
    alSourcef(sourceCity, AL_GAIN, newVolume);
}
