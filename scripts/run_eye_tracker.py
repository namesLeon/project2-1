import time
import argparse
import cv2
import mediapipe as mp

from core.tracking.backends.mediapipe.tracker import MediaPipeEyeTracker


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", type=int, default=0)
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    args = ap.parse_args()

    cap = cv2.VideoCapture(args.device, cv2.CAP_ANY)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    cap.set(cv2.CAP_PROP_FPS, 60)

    # Initialize MediaPipe FaceMesh
    mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,          # iris landmarks
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    # Our new tracker that already smooths and writes gaze_out.txt
    tracker = MediaPipeEyeTracker(smoothing=0.7, window_size=5)

    cv2.namedWindow("Eye Tracker", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Eye Tracker", 960, 540)

    last = time.time()
    fps = 0.0

    while True:
        ok, frame_bgr = cap.read()
        if not ok:
            print("⚠️  Cannot read from camera.")
            break

        # Convert to RGB for MediaPipe
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

        # Process frame; returns the tracker itself as 'g'
        g = tracker.process(frame_rgb, mp_face_mesh)

        # g.gaze_xy is normalized [0, 1] and already written to gaze_out.txt
        # Draw a simple overlay: a circle at the gaze location + FPS text.
        gx, gy = g.gaze_xy

        if 0.0 <= gx <= 1.0 and 0.0 <= gy <= 1.0:
            h, w, _ = frame_bgr.shape
            px = int(gx * w)
            py = int(gy * h)
            # circle at gaze position
            cv2.circle(frame_bgr, (px, py), 10, (0, 255, 0), 2)

        # FPS estimate
        now = time.time()
        dt = now - last
        last = now
        if dt > 0:
            fps = 0.9 * fps + 0.1 * (1.0 / dt) if fps > 0 else (1.0 / dt)

        cv2.putText(
            frame_bgr,
            f"FPS: {fps:.1f}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 255, 255),
            2,
            cv2.LINE_AA,
        )

        cv2.imshow("Eye Tracker", frame_bgr)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == 27:  # q or ESC
            break

    cap.release()
    mp_face_mesh.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
