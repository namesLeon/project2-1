from pathlib import Path
from typing import Optional, Tuple
import cv2
import numpy as np


def load_cascade(name: str) -> cv2.CascadeClassifier:
    """Loads a Haar cascade from file or fallsback to OpenCV"""
    here = Path(__file__).parent / "resources"
    local = here / name
    if local.exists():
        return cv2.CascadeClassifier(str(local))
    return cv2.CascadeClassifier(str(Path(cv2.data.haarcascades) / name))


def largest_box(boxes) -> Optional[Tuple[int, int, int, int]]:
    """returns the largest box (rectangle) from a list of boxes (rectangles)."""
    if boxes is None or len(boxes) == 0:
        return None
    areas = [w * h for (x, y, w, h) in boxes]
    i = int(np.argmax(areas))
    return tuple(boxes[i])


def make_csrt():
    """creates a new CSRT tracker."""
    ctor_names = ["legacy.TrackerCSRT_create", "TrackerCSRT_create"]
    for name in ctor_names:
        obj = cv2
        ok = True
        for part in name.split("."):
            if not hasattr(obj, part):
                ok = False
                break
            obj = getattr(obj, part)
        if ok and callable(obj):  # if we find the constructor call it and return the CSRT tracker
            return obj()
    return None # otherwise return None

def clamp01(x: float) -> float:
    """
    Forces every float to the [0,1] range. 
    - if x < 0.0, returns 0.0
    - if x > 1.0, returns 1.0
    - else returns x
    """
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


def resolve_screen_size(w: Optional[int], h: Optional[int]) -> tuple[int, int]:
    """tries to find screen size and returns it, or falls back on 1920x1080"""
    if w and h:
        return int(w), int(h)
    try: # uses tkinter to get screen size if w and h are not provided
        import tkinter as _tk
        root = _tk.Tk()
        root.withdraw()
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        root.destroy()
        return int(sw), int(sh)
    except Exception: #return fallback plan
        return 1920, 1080


def eye_roi_from_face_single(face, frame_shape, eye_side: str):
    """
    Returns a single ROI (Region of Interest) for the eye. Taken from the face box.
    If auto then pick the biggest eye ROI.
    """
    # uncover the face box coordinates
    fx, fy, fw, fh = face.x, face.y, face.w, face.h
    H, W = frame_shape[:2]

    # these two crop the the face as eyes are roughly between 28% and 52% of face height
    y0 = int(fy + 0.28 * fh)
    y1 = int(fy + 0.52 * fh)

    # split the face width into left and right eye ROI with same logic as above
    lx0 = int(fx + 0.14 * fw)
    lx1 = int(fx + 0.46 * fw)
    rx0 = int(fx + 0.54 * fw)
    rx1 = int(fx + 0.86 * fw)

    # takes a box defined by two corners and forces it to frame size
    def clamp(x0, y0, x1, y1):
        from ...base import Box 

        # makes sure top left is inside frame
        x0 = max(0, x0)
        y0 = max(0, y0)
        # makes sure bottom right is inside frame
        x1 = min(W - 1, x1)
        y1 = min(H - 1, y1)
        # compute width and height using two corners
        w = max(1, x1 - x0)
        h = max(1, y1 - y0)
        # Return None for boxes that are too small

        return Box(x0, y0, w, h) if (w >= 6 and h >= 6) else None 

    # find the ROIs for left and right eyes or none if too small 
    left = clamp(lx0, y0, lx1, y1)
    right = clamp(rx0, y0, rx1, y1)

    #TODO: look at removing this because we focus on left eye.
    # return according to eye_side parameter (we default to left)
    if eye_side == "left":
        return left
    if eye_side == "right":
        return right
    if left and right:
        return left if (left.w * left.h) >= (right.w * right.h) else right
    return left or right