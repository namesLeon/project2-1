from typing import Optional, List
import cv2
import numpy as np

from ...base import EyeTracker, Gaze, Box
from ...Tracking_Interface import EyeTrackingInterface
from ...Vec2 import Vec2

from .vision_utils import (
    load_cascade,
    largest_box,
    make_csrt,
    eye_roi_from_face_single,
    resolve_screen_size,
    clamp01,
)
from .pupil_proc import pupil_center_precise, pupil_confidence
from .filters import Kalman2D, MedianSmoother
from .calibration import Calibrator


class OpenCVHaarEyeTracker(EyeTracker, EyeTrackingInterface):
    """
    Single-eye tracker which implements EyeTrackingInterface:
      - getNormalizedGazePosition() returns Vec2 between [0,1]
      - getScreenGazePosition() returns Vec2 in pixels
      - isConnected() returns bool
    """

    # eyetracker constructor
    def __init__(
        self,
        min_face: int = 120,
        scale_factor: float = 1.05,
        min_neighbors: int = 5,
        screen_width: Optional[int] = None,
        screen_height: Optional[int] = None,
        eye_side: str = "right",
        smooth_window: int = 5,
        conf_threshold: float = 3.0,
    ):
        # loads OpenCVs face detector
        self.face_cascade = load_cascade("haarcascade_frontalface_default.xml")
        # setting parameters
        self.min_face = min_face
        self.scale_factor = scale_factor
        self.min_neighbors = min_neighbors
        self.face_tracker = None
        self.eye_tracker = None
        self.detect_every = (
            20  # we detect face every 20 frames, apparenltly stops inaccuracy
        )
        self.frame_idx = 0
        self.downscale = 0.5
        self._last_norm_xy: Optional[tuple[float, float]] = None  # normalizing gaze
        self._connected: bool = False  # declare connection status as false
        self.eye_side = (
            eye_side if eye_side in ("right", "left", "auto") else "right"
        )  # sanitization
        # use visual utils which uses tkinter to work out screen resolution, if we cant detect we default to 1920x1080
        self._screen_w, self._screen_h = resolve_screen_size(
            screen_width, screen_height
        )
        # last drawn rectangles that cover face and eye
        self._face_box: Optional[Box] = None
        self._eye_box: Optional[Box] = None
        # using the filter class to make tracking smoother
        self._kf = Kalman2D()  # works on pupil center
        self._smoother = MedianSmoother(window=smooth_window)  # smooths pupil movement

        # calibration
        self._cal = Calibrator()  # maps dx, dy to screen coords
        self.gaze_last: Optional[tuple[float, float]] = (
            None  # keep track of last gaze in dx, dy
        )

        # Thresholds
        self._conf_threshold = conf_threshold

    # --------------- EyeTrackingInterface methods ---------------
    # we use this interface in order to speak to our 3d world
    def getNormalizedGazePosition(self):
        if self._last_norm_xy is None:
            return Vec2(0.5, 0.5)
        x, y = self._last_norm_xy
        return Vec2(clamp01(x), clamp01(y))

    def getScreenGazePosition(self):
        n = self.getNormalizedGazePosition()
        return Vec2(
            float(self._screen_w) * float(n.x), float(self._screen_h) * float(n.y)
        )

    def getSreenGazePosition(self):
        return self.getScreenGazePosition()

    def isConnected(self) -> bool:
        return bool(self._connected)

    # -------------- calibration methods ---------------
    def clear_calibration(self):
        self._cal.clear()  # clears all calibration data

    def add_calibration_sample(self, screen_x: float, screen_y: float):
        if self.gaze_last is None:
            return
        dx, dy = self.gaze_last
        self._cal.add_sample(dx, dy, float(screen_x), float(screen_y))

    # ---------------- main loop ----------------
    def process(self, frame_bgr: np.ndarray) -> Gaze:
        self.frame_idx += 1  # goes to next frame
        gray = cv2.cvtColor(
            frame_bgr, cv2.COLOR_BGR2GRAY
        )  # we make the frame gray because thats what haar cascades use

        # if we have a face box already, we try to track it first otherwise we redect it
        # CSRT = Discriminative Correlation Filter with Channel and Spatial Reliability
        eye_box: Optional[Box] = None
        if self.eye_tracker is not None and self._eye_box is not None:
            ok, bb = self.eye_tracker.update(frame_bgr)
            if ok:
                ex, ey, ew, eh = map(int, [bb[0], bb[1], bb[2], bb[3]])
                eye_box = Box(ex, ey, ew, eh)
            else:
                self.eye_tracker = None

        # if eye is lost we try redetect it we also use it for correcting drift
        need_face = (eye_box is None) or (self.frame_idx % self.detect_every == 0)
        # maintain face detection
        if need_face:
            if self.face_tracker is not None and self._face_box is not None:
                ok, bb = self.face_tracker.update(frame_bgr)
                if ok:
                    fx, fy, fw, fh = map(int, [bb[0], bb[1], bb[2], bb[3]])
                    self._face_box = Box(fx, fy, fw, fh)
                else:
                    self.face_tracker = None
                    self._face_box = None

            # we redetect face with restart CSRT tracker
            # run haar if we dont have a face box or detect every 40 frames
            if self._face_box is None or (
                self.frame_idx % (self.detect_every * 2) == 0
            ):
                small = cv2.resize(
                    gray, (0, 0), fx=self.downscale, fy=self.downscale
                )  # detect on a small image for speed
                # haar detection on small image
                faces = self.face_cascade.detectMultiScale(
                    small,
                    scaleFactor=self.scale_factor,
                    minNeighbors=self.min_neighbors,
                    minSize=(
                        int(self.min_face * self.downscale),
                        int(self.min_face * self.downscale),
                    ),
                )
                # if we have multiples faces pick the largest one
                best = largest_box(faces)
                # now we convert the box back to full size and init tracker
                if best is not None:
                    sx, sy, sw, sh = best
                    fx = int(sx / self.downscale)
                    fy = int(sy / self.downscale)
                    fw = int(sw / self.downscale)
                    fh = int(sh / self.downscale)
                    self._face_box = Box(fx, fy, fw, fh)
                    # restart tracker
                    csrt = make_csrt()
                    if csrt is not None:
                        self.face_tracker = csrt
                        self.face_tracker.init(frame_bgr, (fx, fy, fw, fh))
                else:
                    self._face_box = None

            if self._face_box is not None:
                new_eye = eye_roi_from_face_single(
                    self._face_box, frame_bgr.shape, self.eye_side
                )
                if new_eye is not None:
                    eye_box = new_eye
                    csrt_eye = make_csrt()
                    if csrt_eye is not None:
                        self.eye_tracker = csrt_eye
                        self.eye_tracker.init(
                            frame_bgr, (eye_box.x, eye_box.y, eye_box.w, eye_box.h)
                        )
                    self._eye_box = eye_box
                else:
                    self.eye_tracker = None
                    self._eye_box = None

        if eye_box is None:
            self._connected = False
            return Gaze(ok=False)

        # roi = region of interest
        roi = gray[eye_box.y : eye_box.y + eye_box.h, eye_box.x : eye_box.x + eye_box.w]
        pc = pupil_center_precise(
            roi
        )  # this is where we locate the actual pupil inside the eye box
        if pc is None:
            # if we cant find pupil we disconnect
            self._connected = False
            return Gaze(
                ok=False,
                face=self._face_box,
                left_eye=eye_box,
                right_eye=None,
                left_iris=None,
                right_iris=None,
                gaze_xy=None,
                confidence=0.0,
            )

        # kalman filter application - used to stabilize pupil so its not so jittery
        cx, cy = pc
        cx_f, cy_f = self._kf.step(cx, cy)

        # this is where we reject blinks or pupils that might not be correct
        conf = pupil_confidence(roi, int(cx_f), int(cy_f))
        if conf < self._conf_threshold:
            self._connected = False
            return Gaze(
                ok=False,
                face=self._face_box,
                left_eye=eye_box,
                right_eye=None,
                left_iris=None,
                right_iris=None,
                gaze_xy=None,
                confidence=float(conf),
            )

        # normalize gaze in -1 to 1 range (center is 0,0)
        dx_raw = (cx_f - (eye_box.w / 2.0)) / (eye_box.w / 2.0)
        dy_raw = (cy_f - (eye_box.h / 2.0)) / (eye_box.h / 2.0)
        dx, dy = self._smoother.update(dx_raw, dy_raw)
        self.gaze_last = (float(dx), float(dy))

        # map to screen coordinates
        sx, sy = self._cal.map_to_screen(dx, dy, self._screen_w, self._screen_h)
        self._last_norm_xy = (sx / self._screen_w, sy / self._screen_h)
        self._connected = True

        # we return the gaze object
        return Gaze(
            ok=True,
            face=self._face_box,
            left_eye=eye_box,
            right_eye=None,
            left_iris=(eye_box.x + int(round(cx_f)), eye_box.y + int(round(cy_f))),
            right_iris=None,
            gaze_xy=(float(dx), float(dy)),
            confidence=float(conf),
        )
