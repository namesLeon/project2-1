from typing import List, Optional, Tuple
import numpy as np
from .vision_utils import clamp01


# builds polynomial feature vector
def _poly_features(dx: float, dy: float) -> np.ndarray:
    return np.array(
        [1.0, dx, dy, dx * dx, dx * dy, dy * dy], dtype=np.float64
    )  # returns 6 element numpy array


class Calibrator:
    """
    Stores calibration samples and fits two regressions
    - one for x coordinates (screen_x = f(dx, dy))
    - one for y coordinates (screen_y = g(dx, dy))
    """

    def __init__(self, lam: float = 1e-3):
        # constructor for Calibrator class. 
        self._scr: List[tuple[float, float]] = [] 
        self._pix: List[tuple[float, float]] = []  
        self._Mx: Optional[np.ndarray] = None
        self._My: Optional[np.ndarray] = None
        self._lam = lam

    # erases all samples and fitted models
    def clear(self):
        self._scr.clear()
        self._pix.clear()
        self._Mx = None
        self._My = None

    # adds a calibration pair, casts to float to ensure consistency and tries to fit the model
    def add_sample(
        self, gaze_dx: float, gaze_dy: float, screen_x: float, screen_y: float
    ):
        self._scr.append((float(gaze_dx), float(gaze_dy)))
        self._pix.append((float(screen_x), float(screen_y)))
        self._fit_if_ready()

    # fits if we have at least 4 samples before producing a model
    def _fit_if_ready(self):
        if len(self._scr) < 4:
            self._Mx = None
            self._My = None
            return
        X = np.vstack([_poly_features(dx, dy) for (dx, dy) in self._scr])  # build the design matrix and target vectors

        yx = np.array([p[0] for p in self._pix], dtype=np.float64)  # yx is vector of screen x coords
        yy = np.array([p[1] for p in self._pix], dtype=np.float64)  # yy is vector of screen y coords
        lamI = self._lam * np.eye(X.shape[1])  # makes ridge matrix
        XtX = X.T @ X + lamI
        self._Mx = np.linalg.solve(XtX, X.T @ yx)
        self._My = np.linalg.solve(XtX, X.T @ yy)

    # converts dx,dy (which is between -1,1) to nx,ny (which is between 0,1)
    def map_to_screen(
        self, dx: float, dy: float, screen_w: int, screen_h: int
    ) -> tuple[float, float]:
        # if not calibrated fall back to linear mapping, else build 6 feature vector
        if self._Mx is None or self._My is None:
            nx = clamp01((dx + 1.0) * 0.5)
            ny = clamp01((dy + 1.0) * 0.5)
            return nx * screen_w, ny * screen_h
        f = _poly_features(dx, dy)
        return float(f @ self._Mx), float(f @ self._My)
