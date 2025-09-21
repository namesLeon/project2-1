from dataclasses import dataclass
from typing import Optional, Tuple
import numpy as np

@dataclass
class Box:
    x: int
    y: int
    w: int
    h: int

@dataclass
class Gaze:
    ok: bool
    face: Optional[Box] = None
    left_eye: Optional[Box] = None
    right_eye: Optional[Box] = None
    left_iris: Optional[Tuple[int, int]] = None
    right_iris: Optional[Tuple[int, int]] = None
    gaze_xy: Optional[Tuple[float, float]] = None   # normalized (-1..+1)
    confidence: float = 0.0

class EyeTracker:
    def process(self, frame_bgr: np.ndarray) -> Gaze:
        raise NotImplementedError


