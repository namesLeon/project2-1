from pathlib import Path
from typing import Optional, Tuple, List
from collections import deque
import cv2
import numpy as np
from pathlib import Path

from ...base import EyeTracker, Gaze, Box
from ...tracking_interface import EyeTrackingInterface
from ...Vec2 import Vec2


# -------------------------------
# helpers
# -------------------------------
def _load_cascade(name: str) -> cv2.CascadeClassifier:
    here = Path(__file__).parent / "resources"
    local = here / name
    if local.exists():
        return cv2.CascadeClassifier(str(local))
    return cv2.CascadeClassifier(str(Path(cv2.data.haarcascades) / name))


def _largest_box(boxes) -> Optional[Tuple[int, int, int, int]]:
    if boxes is None or len(boxes) == 0:
        return None
    areas = [w * h for (x, y, w, h) in boxes]
    i = int(np.argmax(areas))
    return tuple(boxes[i])


def _make_csrt():
    ctor_names = ["legacy.TrackerCSRT_create", "TrackerCSRT_create"]
    obj = cv2
    for name in ctor_names:
        obj = cv2
        ok = True
        for part in name.split("."):
            if not hasattr(obj, part):
                ok = False
                break
            obj = getattr(obj, part)
        if ok and callable(obj):
            return obj()
    return None


def _clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


def _eye_roi_from_face_single(face: Box, frame_shape, eye_side: str) -> Box | None:
    """
    Return a single eye ROI: 'left', 'right', or pick the wider one if 'auto'.
    Coordinates are derived as fractions of the detected face box.
    """
    fx, fy, fw, fh = face.x, face.y, face.w, face.h
    H, W = frame_shape[:2]

    y0 = int(fy + 0.28 * fh)
    y1 = int(fy + 0.52 * fh)
    lx0 = int(fx + 0.14 * fw); lx1 = int(fx + 0.46 * fw)
    rx0 = int(fx + 0.54 * fw); rx1 = int(fx + 0.86 * fw)

    def clamp(x0, y0, x1, y1):
        x0 = max(0, x0); y0 = max(0, y0)
        x1 = min(W - 1, x1); y1 = min(H - 1, y1)
        w = max(1, x1 - x0); h = max(1, y1 - y0)
        return Box(x0, y0, w, h) if (w >= 6 and h >= 6) else None

    left = clamp(lx0, y0, lx1, y1)
    right = clamp(rx0, y0, rx1, y1)

    if eye_side == "left":
        return left
    if eye_side == "right":
        return right
    if left and right:
        return left if (left.w * left.h) >= (right.w * right.h) else right
    return left or right


def _suppress_highlights(gray: np.ndarray) -> np.ndarray:
    """Suppress small bright glints using morphological top-hat and inpainting-like blend."""
    se = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, se)
    _, mask = cv2.threshold(tophat, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    mask = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=1)
    suppressed = cv2.inpaint(gray, mask, 3, cv2.INPAINT_TELEA)
    return suppressed


def _subpixel_refine(gray: np.ndarray, pt: Tuple[int, int], win: int = 5) -> Tuple[float, float]:
    """Refine a point to subpixel accuracy around a small window."""
    x, y = pt
    h, w = gray.shape[:2]
    x = max(0, min(w - 1, x))
    y = max(0, min(h - 1, y))
    pts = np.array([[np.float32(x), np.float32(y)]], dtype=np.float32)
    term = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.01)
    try:
        refined = cv2.cornerSubPix(
            gray.astype(np.uint8), pts, (win, win), (-1, -1), term
        )
        return float(refined[0, 0, 0]), float(refined[0, 0, 1])
    except Exception:
        return float(x), float(y)


def _pupil_center_precise(eye_gray: np.ndarray) -> Optional[Tuple[int, int]]:
    """
    High-accuracy pupil center:
      1) CLAHE + bilateral filter + highlight suppression
      2) Edge path: Canny → contours → fitEllipse → dark check
      3) Fallback: binary inversion by percentile + morphology → contour moments
      4) Subpixel refine around best
    Coordinates returned are in the eye_gray coordinate system.
    """
    h, w = eye_gray.shape[:2]
    if h < 10 or w < 10:
        return None

    top_crop = int(0.18 * h)
    g = eye_gray[top_crop:, :]
    if g.size == 0:
        return None

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    g = clahe.apply(g)
    g = cv2.bilateralFilter(g, d=5, sigmaColor=50, sigmaSpace=7)
    g = _suppress_highlights(g)

    v = np.median(g)
    lo = int(max(0, 0.66 * v))
    hi = int(min(255, 1.33 * v))
    edges = cv2.Canny(g, lo, hi, apertureSize=3, L2gradient=True)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    H, W = g.shape[:2]
    area_min = 0.005 * (W * H)
    area_max = 0.25 * (W * H)

    best_pt = None
    best_score = -1.0
    mean_all = float(np.mean(g))

    for c in contours:
        if len(c) < 20:
            continue
        (x, y, ww, hh) = cv2.boundingRect(c)
        area = float(ww * hh)
        if area < area_min or area > area_max:
            continue
        if ww < 4 or hh < 4:
            continue
        try:
            ellipse = cv2.fitEllipse(c)
        except cv2.error:
            continue
        (cx, cy), (MA, ma), _ = ellipse
        if min(MA, ma) < 3:
            continue
        mask = np.zeros_like(g)
        cv2.ellipse(mask, ellipse, 255, -1)
        dark_mean = float(cv2.mean(g, mask=mask)[0])
        circularity = min(MA, ma) / max(MA, ma)
        center_y = cy
        top_penalty = 1.0 - min(1.0, center_y / (0.35 * H)) 
        score = (mean_all - dark_mean) * (0.7 + 0.3 * circularity) - 1.6 * top_penalty
        if score > best_score:
            best_score = score
            best_pt = (int(round(cx)), int(round(cy)))


    if best_pt is None:
        p = np.percentile(g, 12)
        _, th = cv2.threshold(g, int(p), 255, cv2.THRESH_BINARY_INV)
        th = cv2.morphologyEx(th, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8), iterations=1)
        th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8), iterations=1)
        contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            area_min2 = 0.006 * (W * H)
            area_max2 = 0.22 * (W * H)
            best_score = -1.0
            for c in contours:
                area = cv2.contourArea(c)
                if area < area_min2 or area > area_max2:
                    continue
                x, y, ww, hh = cv2.boundingRect(c)
                if x <= 0 or y <= 0 or (x + ww) >= (W - 1) or (y + hh) >= (H - 1):
                    continue
                if y < int(0.10 * H):
                    continue
                perim = cv2.arcLength(c, True)
                if perim <= 1e-6:
                    continue
                circularity = 4.0 * np.pi * area / (perim * perim)
                mask = np.zeros_like(th)
                cv2.drawContours(mask, [c], -1, 255, -1)
                dark_mean = float(cv2.mean(g, mask=mask)[0])
                cy = y + hh / 2.0
                top_penalty = 1.0 - min(1.0, cy / (0.35 * H))
                score = (float(np.mean(g)) - dark_mean) * (0.6 + 0.4 * circularity) - 1.6 * top_penalty
                if score > best_score:
                    M = cv2.moments(c)
                    if M["m00"] > 1e-6:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        best_pt = (cx, cy)

    if best_pt is None:
        return None

    rx, ry = _subpixel_refine(g, best_pt, win=5)
    return (int(round(rx)), int(round(ry + top_crop)))


class OpenCVHaarEyeTracker(EyeTracker, EyeTrackingInterface):
    """
    Single-eye tracker implementing EyeTrackingInterface:
      - getNormalizedGazePosition() -> Vec2 in [0,1]
      - getScreenGazePosition()     -> Vec2 in pixels
      - isConnected()               -> bool

    Tracks one eye ('right' | 'left' | 'auto', default 'right') with accuracy focus.
    """

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
        self.face_cascade = _load_cascade("haarcascade_frontalface_default.xml")
        self.min_face = min_face
        self.scale_factor = scale_factor
        self.min_neighbors = min_neighbors

        self.face_tracker = None
        self.eye_tracker = None
        self.detect_every = 20
        self.frame_idx = 0
        self.downscale = 0.5
 
        self._last_norm_xy: Optional[tuple[float, float]] = None  # [0,1]
        self._connected: bool = False

        self.eye_side = eye_side if eye_side in ("right", "left", "auto") else "right"

        self._screen_w, self._screen_h = self._resolve_screen_size(screen_width, screen_height)

        self._face_box: Optional[Box] = None
        self._eye_box: Optional[Box] = None


        self._kf = None

        self._dx_hist: deque = deque(maxlen=max(1, smooth_window))
        self._dy_hist: deque = deque(maxlen=max(1, smooth_window))


        self._cal_pts_scr: List[tuple[float, float]] = [] 
        self._cal_pts_pix: List[tuple[float, float]] = [] 
        self._cal_Mx: Optional[np.ndarray] = None
        self._cal_My: Optional[np.ndarray] = None 


        self.gaze_last: Optional[tuple[float, float]] = None

        self._conf_threshold = conf_threshold

    def getNormalizedGazePosition(self):
        if self._last_norm_xy is None:
            return Vec2(0.5, 0.5)
        x, y = self._last_norm_xy
        return Vec2(_clamp01(x), _clamp01(y))

    def getScreenGazePosition(self):
        n = self.getNormalizedGazePosition()
        sx = float(self._screen_w) * float(n.x)
        sy = float(self._screen_h) * float(n.y)
        return Vec2(sx, sy)

    def getSreenGazePosition(self):
        return self.getScreenGazePosition()

    def isConnected(self) -> bool:
        return bool(self._connected)

    def clear_calibration(self):
        self._cal_pts_scr.clear()
        self._cal_pts_pix.clear()
        self._cal_Mx = None
        self._cal_My = None

    def add_calibration_sample(self, screen_x: float, screen_y: float):
        if self.gaze_last is None:
            return
        dx, dy = self.gaze_last
        self._cal_pts_scr.append((float(dx), float(dy)))
        self._cal_pts_pix.append((float(screen_x), float(screen_y)))
        self._fit_calibration()

    def process(self, frame_bgr: np.ndarray) -> Gaze:
        self.frame_idx += 1

        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

        eye_box: Optional[Box] = None
        if self.eye_tracker is not None and self._eye_box is not None:
            ok, bb = self.eye_tracker.update(frame_bgr)
            if ok:
                ex, ey, ew, eh = map(int, [bb[0], bb[1], bb[2], bb[3]])
                eye_box = Box(ex, ey, ew, eh)
            else:
                self.eye_tracker = None

        need_face = (eye_box is None) or (self.frame_idx % self.detect_every == 0)
        if need_face:
            if self.face_tracker is not None and self._face_box is not None:
                ok, bb = self.face_tracker.update(frame_bgr)
                if ok:
                    fx, fy, fw, fh = map(int, [bb[0], bb[1], bb[2], bb[3]])
                    self._face_box = Box(fx, fy, fw, fh)
                else:
                    self.face_tracker = None
                    self._face_box = None

            if self._face_box is None or (self.frame_idx % (self.detect_every * 2) == 0):
                small = cv2.resize(gray, (0, 0), fx=self.downscale, fy=self.downscale)
                faces = self.face_cascade.detectMultiScale(
                    small,
                    scaleFactor=self.scale_factor,
                    minNeighbors=self.min_neighbors,
                    minSize=(
                        int(self.min_face * self.downscale),
                        int(self.min_face * self.downscale),
                    ),
                )
                best = _largest_box(faces)
                if best is not None:
                    sx, sy, sw, sh = best
                    fx = int(sx / self.downscale)
                    fy = int(sy / self.downscale)
                    fw = int(sw / self.downscale)
                    fh = int(sh / self.downscale)
                    self._face_box = Box(fx, fy, fw, fh)

                    csrt = _make_csrt()
                    if csrt is not None:
                        self.face_tracker = csrt
                        self.face_tracker.init(frame_bgr, (fx, fy, fw, fh))
                else:
                    self._face_box = None

            
            if self._face_box is not None:
                new_eye = _eye_roi_from_face_single(self._face_box, frame_bgr.shape, self.eye_side)
                if new_eye is not None:
                    eye_box = new_eye
                    csrt_eye = _make_csrt()
                    if csrt_eye is not None:
                        self.eye_tracker = csrt_eye
                        self.eye_tracker.init(frame_bgr, (eye_box.x, eye_box.y, eye_box.w, eye_box.h))
                    self._eye_box = eye_box
                else:
                    self.eye_tracker = None
                    self._eye_box = None

        if eye_box is None:
            self._connected = False
            return Gaze(ok=False)

        roi = gray[eye_box.y: eye_box.y + eye_box.h, eye_box.x: eye_box.x + eye_box.w]
        pc = _pupil_center_precise(roi)
        if pc is None:
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

        cx, cy = pc

        cx_f, cy_f = self._kf_step(cx, cy)

        conf = self._pupil_confidence(roi, int(cx_f), int(cy_f))
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

        dx_raw = (cx_f - (eye_box.w / 2.0)) / (eye_box.w / 2.0)
        dy_raw = (cy_f - (eye_box.h / 2.0)) / (eye_box.h / 2.0)

        dx, dy = self._smooth_dxdy(dx_raw, dy_raw)

        self.gaze_last = (float(dx), float(dy))

        sx, sy = self._map_to_screen(dx, dy)
        self._last_norm_xy = (sx / self._screen_w, sy / self._screen_h)
        self._connected = True

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

    @staticmethod
    def _resolve_screen_size(w: Optional[int], h: Optional[int]) -> tuple[int, int]:
        if w and h:
            return int(w), int(h)
        try:
            import tkinter as _tk
            root = _tk.Tk()
            root.withdraw()
            sw = root.winfo_screenwidth()
            sh = root.winfo_screenheight()
            root.destroy()
            return int(sw), int(sh)
        except Exception:
            return 1920, 1080


    def _ensure_kf(self, cx: float, cy: float):
        kf = cv2.KalmanFilter(4, 2, 0)
        dt = 1.0 / 60.0
        kf.transitionMatrix = np.array([[1, 0, dt, 0],
                                        [0, 1, 0, dt],
                                        [0, 0, 1, 0],
                                        [0, 0, 0, 1]], np.float32)
        kf.measurementMatrix = np.array([[1, 0, 0, 0],
                                         [0, 1, 0, 0]], np.float32)
        q = 1e-2
        r = 2.0
        kf.processNoiseCov = np.eye(4, dtype=np.float32) * q
        kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * r
        kf.errorCovPost = np.eye(4, dtype=np.float32)
        kf.statePost = np.array([[cx], [cy], [0], [0]], np.float32)
        self._kf = kf

    def _kf_step(self, cx: float, cy: float) -> tuple[float, float]:
        if self._kf is None:
            self._ensure_kf(cx, cy)
        pred = self._kf.predict()
        meas = np.array([[np.float32(cx)], [np.float32(cy)]])
        est = self._kf.correct(meas)
        return float(est[0]), float(est[1])

    @staticmethod
    def _pupil_confidence(g: np.ndarray, cx: int, cy: int) -> float:
        h, w = g.shape[:2]
        r = max(3, int(0.06 * min(h, w)))
        yy, xx = np.ogrid[:h, :w]
        mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r
        if not np.any(mask):
            return 0.0
        inside = float(np.mean(g[mask]))
        border = float(np.mean(g[~mask])) if np.any(~mask) else inside
        score = max(0.0, (border - inside))
        return score

    def _smooth_dxdy(self, dx: float, dy: float) -> tuple[float, float]:
        self._dx_hist.append(float(dx))
        self._dy_hist.append(float(dy))
        dx_s = float(np.median(self._dx_hist))
        dy_s = float(np.median(self._dy_hist))
        return dx_s, dy_s

    @staticmethod
    def _poly_features(dx: float, dy: float) -> np.ndarray:
        return np.array([1.0, dx, dy, dx * dx, dx * dy, dy * dy], dtype=np.float64)

    def _fit_calibration(self):
        if len(self._cal_pts_scr) < 4:  
            self._cal_Mx = None
            self._cal_My = None
            return
        X = np.vstack([self._poly_features(dx, dy) for (dx, dy) in self._cal_pts_scr])
        yx = np.array([p[0] for p in self._cal_pts_pix], dtype=np.float64)
        yy = np.array([p[1] for p in self._cal_pts_pix], dtype=np.float64)
        lam = 1e-3
        XtX = X.T @ X + lam * np.eye(X.shape[1])
        self._cal_Mx = np.linalg.solve(XtX, X.T @ yx)
        self._cal_My = np.linalg.solve(XtX, X.T @ yy)

    def _map_to_screen(self, dx: float, dy: float) -> tuple[float, float]:
        if self._cal_Mx is None or self._cal_My is None:
            nx = _clamp01((dx + 1.0) * 0.5)
            ny = _clamp01((dy + 1.0) * 0.5)
            return nx * self._screen_w, ny * self._screen_h
        f = self._poly_features(dx, dy)
        sx = float(f @ self._cal_Mx)
        sy = float(f @ self._cal_My)
        return sx, sy
    def print_normalized_gaze(self, decimals: int = 3) -> str:
        n = self.getNormalizedGazePosition()
        out = f"normalized-Eye-Gaze-positions: x:{n.x:.{decimals}f} y:{n.y:.{decimals}f}"
        print(out)
        return out
    def _write_gaze_for_cpp(self):
        n = self.getNormalizedGazePosition()
        Path("gaze_out.txt").write_text(
        f"normalized-Eye-Gaze-positions: x:{n.x:.6f} y:{n.y:.6f}",
        encoding="utf-8"
    )