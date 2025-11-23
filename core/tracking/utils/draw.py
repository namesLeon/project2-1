import cv2
from mediapipe import solutions as mp

def draw_gaze_overlay(img, fps: float | None = None):
    if fps is not None:
        cv2.putText(img, f"FPS: {fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2, cv2.LINE_AA)

def drawFaceMesh(frame, landmarks):
    mp.drawing_utils.draw_landmarks(
        image=frame,
        landmark_list=landmarks,
        connections=mp.face_mesh.FACEMESH_TESSELATION,
        landmark_drawing_spec=None,
        connection_drawing_spec=mp.drawing_utils.DrawingSpec(color=(255, 0, 0), thickness=1, circle_radius=1)
    )

def drawIris(frame, irisCoords):
    h, w, _ = frame.shape
    coords = (int(irisCoords.x * w), int(irisCoords.y * h))

    cv2.circle(frame, coords, 2, (0, 0, 255), -1)