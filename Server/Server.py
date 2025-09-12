import socket
import sys

def server_start():
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        server_socket.bind(('127.0.0.1', 5050))
        server_socket.listen(5)  
        
        print("Server listen on poort 5050...")
        
        while True:
            (client_socket, client_address) = server_socket.accept()
            print(f"Connected with {client_address}")
            # we want here to send over our vec2 object as string
            try:
                client_name = client_socket.recv(1024).decode('utf-8')
                print(f"Connected: {client_name}")
                
                what_to_send = f'Hallo {client_name}'
                client_socket.send(what_to_send.encode('utf-8'))
                
                
            except Exception as e:
                print(f"Error with communication: {e}")
            finally:
                client_socket.close()
                print("Connection closed.")
                
    except Exception as e:
        print(f"Server Error: {e}")
        raise

def main():
    try:
        server_start()
    except KeyboardInterrupt:
        print("\nServer Shutdown...")
        sys.exit(0)
    except Exception as e:
        print(f"Exception error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()