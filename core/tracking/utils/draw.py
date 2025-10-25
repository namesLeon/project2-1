import cv2
from . .base import Box, Gaze  

def draw_box(img, box: Box, color=(0, 255, 0), thick=2):
    if not box: return
    cv2.rectangle(img, (box.x, box.y), (box.x + box.w, box.y + box.h), color, thick)

def draw_point(img, pt, color=(0, 0, 255), r=3):
    if not pt: return
    cv2.circle(img, pt, r, color, -1, lineType=cv2.LINE_AA)

def draw_gaze_overlay(img, g: Gaze, fps: float | None = None):
    draw_box(img, g.face, (0, 200, 255))
    draw_box(img, g.left_eye, (0, 255, 0))
    draw_box(img, g.right_eye, (0, 255, 0))
    if g.left_iris:  draw_point(img, g.left_iris)
    if g.right_iris: draw_point(img, g.right_iris)
    if g.gaze_xy:
        h, w = img.shape[:2]
        x = int((g.gaze_xy[0] * 0.5 + 0.5) * w)
        y = int((g.gaze_xy[1] * 0.5 + 0.5) * h)
        # cv2.drawMarker(img, (x, y), (255, 0, 0), markerType=cv2.MARKER_CROSS, markerSize=12, thickness=2)
    if fps is not None:
        cv2.putText(img, f"FPS: {fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2, cv2.LINE_AA)
