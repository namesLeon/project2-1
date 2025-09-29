#ifdef _WIN32
    #define WIN32_LEAN_AND_MEAN
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #pragma comment(lib, "ws2_32.lib")
    #define CLOSE_SOCKET closesocket
#else
    #include <sys/socket.h>
    #include <netinet/in.h>
    #include <arpa/inet.h>
    #include <unistd.h>
    #define CLOSE_SOCKET close
    typedef int SOCKET;
    #define INVALID_SOCKET -1
    #define SOCKET_ERROR -1
#endif

#include <iostream>
#include <string>
#include <cstring>
#include <sstream>

struct Vec2 {
    float x;
    float y;
};

void run() {
    // --- Initialize Winsock on Windows ---
    #ifdef _WIN32
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        std::cerr << "WSAStartup failed" << std::endl;
        return;
    }
    #endif

    std::cout << "Client starting..." << std::endl;

    // --- Create socket ---
    SOCKET client_socket = socket(AF_INET, SOCK_STREAM, 0);
    if (client_socket == INVALID_SOCKET) {
        std::cerr << "Socket creation failed" << std::endl;
        #ifdef _WIN32
        WSACleanup();
        #endif
        return;
    }

    // --- Server address ---
    sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(5050);
    inet_pton(AF_INET, "127.0.0.1", &server_addr.sin_addr);

    // --- Connect to server ---
    if (connect(client_socket, (sockaddr*)&server_addr, sizeof(server_addr)) == SOCKET_ERROR) {
        std::cerr << "Connection failed" << std::endl;
        CLOSE_SOCKET(client_socket);
        #ifdef _WIN32
        WSACleanup();
        #endif
        return;
    }

    std::cout << "Connected to server!" << std::endl;

    // --- Send name to server ---
    std::cout << "Enter your name: ";
    std::string name;
    std::getline(std::cin, name);
    send(client_socket, name.c_str(), name.size(), 0);

    // --- Receive welcome message once ---
    char buffer[1024];
    int bytes_received = recv(client_socket, buffer, sizeof(buffer) - 1, 0);
    if (bytes_received > 0) {
        buffer[bytes_received] = '\0';
        std::cout << "Server says: " << buffer << std::endl;
    }

    // --- Continuous receiving loop for Vec2 positions ---
    Vec2 latestPos{0.0f, 0.0f};
    std::cout << "Receiving gaze data..." << std::endl;

    while (true) {
        bytes_received = recv(client_socket, buffer, sizeof(buffer) - 1, 0);
        if (bytes_received <= 0) {
            std::cerr << "Disconnected from server" << std::endl;
            break;
        }

        buffer[bytes_received] = '\0';
        std::string data(buffer);

        // --- Parse "x,y" into floats ---
        std::stringstream ss(data);
        std::string sx, sy;
        if (std::getline(ss, sx, ',') && std::getline(ss, sy)) {
            try {
                latestPos.x = std::stof(sx);
                latestPos.y = std::stof(sy);

                // Debug print
                std::cout << "Gaze position: (" << latestPos.x << ", " << latestPos.y << ")" << std::endl;

                // TODO: Pass latestPos.x & latestPos.y to your shader project here

            } catch (...) {
                std::cerr << "Invalid data format: " << data << std::endl;
            }
        }
    }

    // --- Cleanup ---
    CLOSE_SOCKET(client_socket);
    #ifdef _WIN32
    WSACleanup();
    #endif
}
