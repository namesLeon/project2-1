import cv2
import mediapipe as mp
import socket
import struct

# UDP setup
UDP_IP = "127.0.0.1"
UDP_PORT = 5052
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Mediapipe setup
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5)

cap = cv2.VideoCapture(0)

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        continue
    
    frame.flags.writeable = False
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = face_mesh.process(rgb_frame)

    if result.multi_face_landmarks:
        # Take first detected face
        face = result.multi_face_landmarks[0]

        #Iris landmark indices (from MediaPipe docs)
        left_iris = face.landmark[468]
        #right_iris = face.landmark[473]
        #nose = face.landmark[1]  # nose tip (approx head center)

        #eye_x = (left_iris.x + right_iris.x) / 2
        #eye_y = (left_iris.y + right_iris.y) / 2
        #eye_z = (left_iris.z + right_iris.z) / 2

        #normalize to screen space [-1,1]
        x = (left_iris.x - 0.5) * 2  # 0.0 → -1, 0.5 → 0, 1.0 → +1
        y = (left_iris.y - 0.5) * 2  # 0.0 → -1, 0.5 → 0, 1.0 → +1 + flip vertical
        z = (left_iris.z)  # relative depth from camera

        # Send as floats
        message = struct.pack('fff', x, y, z)
        sock.sendto(message, (UDP_IP, UDP_PORT))
        #sock.sendto(message, (UDP_IP, 5053))

    # Show simple preview (press ESC to quit)
    cv2.imshow("Tracking", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
