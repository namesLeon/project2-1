import time
import argparse
import cv2
import mediapipe as mp

from core.tracking.backends.mediapipe.tracker import MediaPipeEyeTracker
from core.tracking.utils.mediaPipeDraw import MediaPipeDraw


def main(): #runs camera loop
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", type=int, default=0) #0 = default webcam
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    args = ap.parse_args()

    cap = cv2.VideoCapture(args.device, cv2.CAP_ANY) #open camera
    cap.set(cv2.CAP_PROP_FPS, 60)

    mp_face_mesh = mp.solutions.face_mesh.FaceMesh( #initiate facemesh
        max_num_faces=1, 
        refine_landmarks=True,         
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    tracker = MediaPipeEyeTracker(smoothing=0.7, window_size=5) #apply smoother to tracker

    cv2.namedWindow("Eye Tracker", cv2.WINDOW_NORMAL)

    last = time.time() # last frame 
    fps = 0.0

    draw = MediaPipeDraw()
    draw.toggleGazeVisuals() #gaze circle is drawn by default

    while True: #main loop
        ok, frame_bgr = cap.read() #read first frame
        if not ok:
            print("⚠️  Cannot read from camera.")
            break

        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB) 

        #convert BGR to RGB so mediapipe can use it
        g = tracker.process(frame_rgb, mp_face_mesh)

        #get normalized gaze
        gx, gy = g.gaze_xy

        if 0.0 <= gx <= 1.0 and 0.0 <= gy <= 1.0: #only draws gaze if its inside the range
            h, w, _ = frame_bgr.shape
            px = int(gx * w)
            py = int(gy * h)
            draw.drawGaze(frame_bgr, (px, py))

        now = time.time() #current timestamp for fps
        dt = now - last #time between last frame and now
        last = now
        
        #prevent div by 0
        if dt > 0:
            fps = 0.9 * fps + 0.1 * (1.0 / dt) if fps > 0 else (1.0 / dt)

        draw.drawFPS(frame_bgr, fps) # draw the FPS on screen

        cv2.imshow("Eye Tracker", frame_bgr) #display frame

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == 27:  #q or ESC to exit
            break
        elif key == ord("v"):  # v
            draw.toggleGazeVisuals()

    cap.release() #realease the camera device
    mp_face_mesh.close() #free mediapipe resources
    cv2.destroyAllWindows() #close all



if __name__ == "__main__":
    main()
