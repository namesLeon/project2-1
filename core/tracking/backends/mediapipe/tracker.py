from pathlib import Path
from collections import deque

LEFT_IRIS_CENTER_IDX = 468
RIGHT_IRIS_CENTER_IDX = 473

GAZE_FILE = Path("gaze_out.txt")


class MediaPipeEyeTracker:

    def __init__(self, smoothing: float = 0.7, window_size: int = 5) -> None:
        self.gaze_xy: tuple[float, float] = (0.0, 0.0)

        self.left_gaze_xy: tuple[float, float] = (0.0, 0.0)
        self.right_gaze_xy: tuple[float, float] = (0.0, 0.0)

        self._window = deque(maxlen=window_size)

        self.smoothing = smoothing
        self._has_prev_gaze = False

    def process(self, frame_rgb, faceMesh):
        results = faceMesh.process(frame_rgb)

        if not results.multi_face_landmarks:
            return self

        landmarks = results.multi_face_landmarks[0]

        if len(landmarks.landmark) <= RIGHT_IRIS_CENTER_IDX:
            return self

        left_iris = landmarks.landmark[LEFT_IRIS_CENTER_IDX]
        right_iris = landmarks.landmark[RIGHT_IRIS_CENTER_IDX]

        lx, ly = left_iris.x, left_iris.y
        rx, ry = right_iris.x, right_iris.y

        self.left_gaze_xy = (lx, ly)
        self.right_gaze_xy = (rx, ry)

        cx = (lx + rx) * 0.5
        cy = (ly + ry) * 0.5

        self._window.append((cx, cy))

        wx = sum(p[0] for p in self._window) / len(self._window)
        wy = sum(p[1] for p in self._window) / len(self._window)

        if not self._has_prev_gaze:
            smoothed_x, smoothed_y = wx, wy
            self._has_prev_gaze = True
        else:
            prev_x, prev_y = self.gaze_xy
            alpha = self.smoothing
            smoothed_x = alpha * prev_x + (1.0 - alpha) * wx
            smoothed_y = alpha * prev_y + (1.0 - alpha) * wy

        self.gaze_xy = (smoothed_x, smoothed_y)
        self.write_gaze_for_cpp()

        return self

    def write_gaze_for_cpp(self) -> None:
        GAZE_FILE.write_text(
            f"normalized-Eye-Gaze-positions: x:{self.gaze_xy[0]:.6f} "
            f"y:{self.gaze_xy[1]:.6f}\n",
            encoding="utf-8",
        )
