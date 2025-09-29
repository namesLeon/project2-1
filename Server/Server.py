import socket
import sys, os 
import threading
import time
sys.path.append(os.path.abspath(".."))
import pyautogui  
from tracker import OpenCVHaarEyeTracker  # your tracker class
from Vec2 import Vec2

HOST = '127.0.0.1'
PORT = 5050

clients = []
tracker = OpenCVHaarEyeTracker()

def handle_client(client_socket, addr):
    print(f"[INFO] Client connected: {addr}")
    clients.append(client_socket)
    try:
        name = client_socket.recv(1024).decode('utf-8')
        print(f"[INFO] Client name: {name}")
        client_socket.send(f"Welcome {name}".encode('utf-8'))
    except Exception as e:
        print(f"[ERROR] Client communication failed: {e}")
    # Do not close here → keep connection open for broadcasts

def broadcast_positions():
    while True:
        try:
            if tracker.isConnected():
                pos = tracker.getScreenGazePosition()
            else:
                x, y = pyautogui.position()
                pos = Vec2(x, y)

            data = f"{pos.x:.2f},{pos.y:.2f}"
            print(f"[DEBUG] Sending: {data}")

            # Send to all connected clients
            for c in clients[:]:
                try:
                    c.send(data.encode('utf-8'))
                except Exception as e:
                    print(f"[WARN] Client disconnected: {e}")
                    clients.remove(c)

            time.sleep(0.05)  # 20 FPS

        except Exception as e:
            print(f"[ERROR] Broadcast loop: {e}")
            time.sleep(1)

def server_start():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)

    print(f"[INFO] Server listening on {HOST}:{PORT}")

    # Start broadcasting thread
    threading.Thread(target=broadcast_positions, daemon=True).start()

    while True:
        client_socket, addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True).start()

def main():
    try:
        server_start()
    except KeyboardInterrupt:
        print("\n[INFO] Server shutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
