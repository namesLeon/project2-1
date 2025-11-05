import time
import argparse
import cv2

from core.tracking.backends.opencv_haar.tracker import OpenCVHaarEyeTracker
from core.tracking.utils.draw import draw_gaze_overlay
from core.tracking.postprocess.CircleSmoothing import CircleSmooth
from core.tracking.postprocess.EMASmoothing import EMA
smoother = CircleSmooth()
smoother2 = EMA(0.35)




def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", type=int, default=0)
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    ap.add_argument("--min_face", type=int, default=120)
    args = ap.parse_args()

    cap = cv2.VideoCapture(args.device, cv2.CAP_ANY)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    cap.set(cv2.CAP_PROP_FPS, 60)

    tracker = OpenCVHaarEyeTracker(min_face=args.min_face)

    cv2.namedWindow("Eye Tracker", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Eye Tracker", 960, 540)

    last = time.time()
    fps = 0.0

    while True:
        ok, frame = cap.read()
        if not ok:
            print("⚠️  Cannot read from camera.")
            break

        g = tracker.process(frame)
        g.gaze_xy = smoother.update(g.gaze_xy)
        g.gaze_xy = smoother2.update(g.gaze_xy)
        now = time.time()
        dt = now - last
        last = now
        if dt > 0:
            fps = 0.9*fps + 0.1*(1.0/dt) if fps > 0 else (1.0/dt)

        draw_gaze_overlay(frame, g, fps=fps)
        cv2.imshow("Eye Tracker", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:  # q or ESC
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
