import time
import argparse
import cv2

from core.tracking.backends.mediapipe.tracker import MediaPipeEyeTracker
from core.tracking.utils.draw import draw_gaze_overlay
from mediapipe import solutions as mp




def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", type=int, default=0)
    ap.add_argument("--width", type=int, default=800)
    ap.add_argument("--height", type=int, default=600)
    args = ap.parse_args()

    cap = cv2.VideoCapture(args.device, cv2.CAP_ANY)
    cap.set(cv2.CAP_PROP_FPS, 60)

    tracker = MediaPipeEyeTracker()

    cv2.namedWindow("Eye Tracker", cv2.WINDOW_NORMAL)

    last = time.time()
    fps = 0.0

    with (mp.face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as faceMesh):

        while cap.isOpened():
            ok, frame = cap.read()
            frame = cv2.resize(frame, (args.width, args.height), interpolation=cv2.INTER_CUBIC)
            if not ok:
                print("⚠️  Cannot read from camera.")
                break

            tracker.process(frame, faceMesh)

            now = time.time()
            dt = now - last
            last = now
            if dt > 0:
                fps = 0.9 * fps + 0.1 * (1.0 / dt) if fps > 0 else (1.0 / dt)

            draw_gaze_overlay(frame, fps=fps)
            cv2.imshow("Eye Tracker", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:  # q or ESC
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
