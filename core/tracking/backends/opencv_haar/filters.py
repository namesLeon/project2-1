from collections import deque
from typing import Tuple
import numpy as np
import cv2


class Kalman2D:
    """Kalman filter for pupil tracking to reduce jitter"""

    def __init__(
        self, dt: float = 1.0 / 60.0, q: float = 1e-2, r: float = 2.0
    ):  # assuming 60FPS,
        self.kf = cv2.KalmanFilter(4, 2, 0)
        self.kf.transitionMatrix = np.array(
            [[1, 0, dt, 0], [0, 1, 0, dt], [0, 0, 1, 0], [0, 0, 0, 1]], np.float32
        )
        self.kf.measurementMatrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], np.float32)
        self.kf.processNoiseCov = np.eye(4, dtype=np.float32) * q  # process noise
        self.kf.measurementNoiseCov = (
            np.eye(2, dtype=np.float32) * r
        )  # measurement noise
        self.kf.errorCovPost = np.eye(4, dtype=np.float32)
        self.initialized = False

    # on first run set state to current measurement with 0 velocity
    def ensure(self, cx: float, cy: float):
        if not self.initialized:
            self.kf.statePost = np.array([[cx], [cy], [0], [0]], np.float32)
            self.initialized = True

    # performs a prediction and correction step
    def step(self, cx: float, cy: float) -> Tuple[float, float]:
        if not self.initialized:
            self.ensure(cx, cy)
        self.kf.predict()  # prediction step
        est = self.kf.correct(
            np.array([[np.float32(cx)], [np.float32(cy)]])
        )  # correction step
        return float(est[0]), float(
            est[1]
        )  # returns the filtered x,y from updated state


class MedianSmoother:
    """Median smoother for normalized dx/dy to reduce jitter."""
    # constructor for MedianSmoother class
    def __init__(self, window: int = 5):
        self.dx = deque(maxlen=max(1, window))
        self.dy = deque(maxlen=max(1, window))

    # updates the smoother with new dx,dy and returns the smoothed values
    def update(self, dx: float, dy: float) -> Tuple[float, float]:
        self.dx.append(float(dx))
        self.dy.append(float(dy))
        return float(np.median(self.dx)), float(np.median(self.dy))
