from pathlib import Path
from typing import Optional, Tuple
import cv2
import numpy as np

from ...base import EyeTracker, Gaze, Box


# helpers 
def _load_cascade(name: str) -> cv2.CascadeClassifier:
    """Try vendored resources/ first, then fall back to OpenCV's built-ins."""
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
    """Create a CSRT tracker across OpenCV builds."""
    ctor_names = ["legacy.TrackerCSRT_create", "TrackerCSRT_create"]
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


def _eye_rois_from_face(face: Box, frame_shape) -> tuple[Box | None, Box | None]:
    fx, fy, fw, fh = face.x, face.y, face.w, face.h
    H, W = frame_shape[:2]

    # shift downward: eyes will be roughly in the middle third keeps eye brows out
    y0 = int(fy + 0.28 * fh)
    y1 = int(fy + 0.52 * fh)
    lx0 = int(fx + 0.14 * fw); lx1 = int(fx + 0.46 * fw)
    rx0 = int(fx + 0.54 * fw); rx1 = int(fx + 0.86 * fw)

    def clamp(x0, y0, x1, y1):
        x0 = max(0, x0); y0 = max(0, y0)
        x1 = min(W - 1, x1); y1 = min(H - 1, y1)
        w = max(1, x1 - x0); h = max(1, y1 - y0)
        return Box(x0, y0, w, h) if w >= 4 and h >= 4 else None

    return clamp(lx0, y0, lx1, y1), clamp(rx0, y0, rx1, y1)


def _pupil_center(eye_gray: np.ndarray) -> Optional[tuple[int,int]]:
    h, w = eye_gray.shape[:2]
    if h < 8 or w < 8:
        return None

    top_crop = int(0.22 * h)
    work = eye_gray[top_crop:, :]
    if work.size == 0:
        return None

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    g = clahe.apply(work)
    g = cv2.GaussianBlur(g, (5,5), 0)

    p10 = np.percentile(g, 12) 
    _, th = cv2.threshold(g, int(p10), 255, cv2.THRESH_BINARY_INV)

    th = cv2.morphologyEx(th, cv2.MORPH_OPEN, np.ones((3,3), np.uint8), iterations=1)
    th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, np.ones((3,3), np.uint8), iterations=1)

    contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    H, W = work.shape[:2]
    area_min = 0.006 * (W * H)
    area_max = 0.20  * (W * H)

    best = None
    best_score = -1.0
    mean_all = float(np.mean(g))

    for c in contours:
        area = cv2.contourArea(c)
        if area < area_min or area > area_max:
            continue
        x, y, ww, hh = cv2.boundingRect(c)

      
        if x <= 0 or y <= 0 or (x+ww) >= (W-1) or (y+hh) >= (H-1):
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

        cy = y + hh/2.0
        top_penalty = 1.0 - min(1.0, cy / (0.35 * H))  
        score = (mean_all - dark_mean) * (0.6 + 0.4 * circularity) - 2.0 * top_penalty

        if score > best_score:
            M = cv2.moments(c)
            if M["m00"] > 1e-6:
                cx = int(M["m10"]/M["m00"])
                cy = int(M["m01"]/M["m00"])
                best = (cx, cy + top_crop)  
                best_score = score

    if best is None:
        circles = cv2.HoughCircles(
            g, cv2.HOUGH_GRADIENT, dp=1.5, minDist=max(6, int(0.3*min(H, W))),
            param1=100, param2=8,
            minRadius=int(0.07*min(H, W)), maxRadius=int(0.25*min(H, W))
        )
        if circles is not None and len(circles[0]) > 0:
            c0 = circles[0][0]
            return (int(c0[0]), int(c0[1]) + top_crop)

    return best



# tracker 

class OpenCVHaarEyeTracker(EyeTracker):
    def __init__(
        self,
        min_face: int = 120,
        eye_padding: float = 0.20,  
        scale_factor: float = 1.05, 
        min_neighbors: int = 5,
    ):
        self.face_cascade = _load_cascade("haarcascade_frontalface_default.xml")
        self.min_face = min_face
        self.eye_padding = eye_padding
        self.scale_factor = scale_factor
        self.min_neighbors = min_neighbors


        self.face_tracker = None
        self.detect_every = 15   # re-detect every 15 frames
        self.frame_idx = 0
        self.downscale = 0.5     

    def process(self, frame_bgr: np.ndarray) -> Gaze:
        self.frame_idx += 1

        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        updated_from_tracker = False
        face_box: Optional[Box] = None
        if self.face_tracker is not None:
            ok, bb = self.face_tracker.update(frame_bgr)
            if ok:
                fx, fy, fw, fh = map(int, [bb[0], bb[1], bb[2], bb[3]])
                face_box = Box(fx, fy, fw, fh)
                updated_from_tracker = True
            else:
                self.face_tracker = None

        if (not updated_from_tracker) or (self.frame_idx % self.detect_every == 0):
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
            if best is None:
                return Gaze(ok=False)

            sx, sy, sw, sh = best
            fx = int(sx / self.downscale)
            fy = int(sy / self.downscale)
            fw = int(sw / self.downscale)
            fh = int(sh / self.downscale)
            face_box = Box(fx, fy, fw, fh)

            csrt = _make_csrt()
            if csrt is not None:
                self.face_tracker = csrt
                self.face_tracker.init(frame_bgr, (fx, fy, fw, fh))
            else:
                self.face_tracker = None

        if face_box is None:
            return Gaze(ok=False)

        left_eye_box, right_eye_box = _eye_rois_from_face(face_box, frame_bgr.shape)

        def eye_center(box: Optional[Box]) -> Optional[Tuple[int, int]]:
            if not box:
                return None
            roi = gray[box.y : box.y + box.h, box.x : box.x + box.w]
            pc = _pupil_center(roi)
            if pc is None:
                return None
            return (box.x + pc[0], box.y + pc[1])

        left_iris = eye_center(left_eye_box)
        right_iris = eye_center(right_eye_box)

        gaze_xy = None
        conf = 0.0
        norms = []
        for box, iris in ((left_eye_box, left_iris), (right_eye_box, right_iris)):
            if box and iris:
                dx = (iris[0] - (box.x + box.w / 2.0)) / (box.w / 2.0)
                dy = (iris[1] - (box.y + box.h / 2.0)) / (box.h / 2.0)
                norms.append((dx, dy))
        if norms:
            ax = float(np.mean([n[0] for n in norms]))
            ay = float(np.mean([n[1] for n in norms]))
            gaze_xy = (max(-1.0, min(1.0, ax)), max(-1.0, min(1.0, ay)))
            conf = len(norms) / 2.0  

        return Gaze(
            ok=True,
            face=face_box,
            left_eye=left_eye_box,
            right_eye=right_eye_box,
            left_iris=left_iris,
            right_iris=right_iris,
            gaze_xy=gaze_xy,
            confidence=conf,
        )
