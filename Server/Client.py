import socket
# The client will be setup in c++ later on, but for now we can test with python
# we want to send vec2 to the c++ client such that we can do calculations there and run in real time
def test_client():
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('127.0.0.1', 5050))
        

        # For now it will return a dummy message, but we can implement a protocol later, such that it will sent vec2
        message = "Put your message here"
        client_socket.send(message.encode('utf-8'))
        
        response = client_socket.recv(1024).decode('utf-8')
        print(f"Server reseponse: {response}")
        
        client_socket.close()
        
    except Exception as e:
        print(f"Client fout: {e}")

if __name__ == "__main__":
    test_client()