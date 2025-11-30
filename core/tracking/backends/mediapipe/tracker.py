from pathlib import Path
from collections import deque

LEFT_IRIS_CENTER_IDX = 468
RIGHT_IRIS_CENTER_IDX = 473

GAZE_FILE = Path("gaze_out.txt")

# new version of eye tracker using facemesh
class MediaPipeEyeTracker:

    # constructor
    def __init__(self, smoothing: float = 0.7, window_size: int = 5) -> None:
        #smoothes coordinates normalized to [0,1]
        self.gaze_xy: tuple[float, float] = (0.0, 0.0)

        self.left_gaze_xy: tuple[float, float] = (0.0, 0.0)
        self.right_gaze_xy: tuple[float, float] = (0.0, 0.0)

        self._window = deque(maxlen=window_size)

        self.smoothing = smoothing

        #we will use this to see if ta previous gaze exists, obviously starts off at false
        self._has_prev_gaze = False

    #processes a single frame
    def process(self, frame_rgb, faceMesh):
        #runs the facemesh 
        results = faceMesh.process(frame_rgb)

        #checks if multiple faces are detected
        if not results.multi_face_landmarks:
            return self

        #takes first detected face
        landmarks = results.multi_face_landmarks[0]

        if len(landmarks.landmark) <= RIGHT_IRIS_CENTER_IDX:
            return self

        left_iris = landmarks.landmark[LEFT_IRIS_CENTER_IDX]
        right_iris = landmarks.landmark[RIGHT_IRIS_CENTER_IDX]

        #reads normalized coordinates from mediapipe
        lx, ly = left_iris.x, left_iris.y #left iris x and y
        rx, ry = right_iris.x, right_iris.y #right iris x and y

        #stores eye positions
        self.left_gaze_xy = (lx, ly)
        self.right_gaze_xy = (rx, ry)

        #works out combined gaze point, again l for left and r for right
        cx = (lx + rx) * 0.5
        cy = (ly + ry) * 0.5

        self._window.append((cx, cy))

        #wx is mean of all x values in _window
        wx = sum(p[0] for p in self._window) / len(self._window)
        #wy is the mean of all y values
        wy = sum(p[1] for p in self._window) / len(self._window)

        #if this is the first time we have a gaze, we set the smooth gaze to the window mean
        if not self._has_prev_gaze:
            smoothed_x, smoothed_y = wx, wy
            self._has_prev_gaze = True
        #otherwise read previous values from self.gaze
        else:
            prev_x, prev_y = self.gaze_xy
            alpha = self.smoothing
            #exponential moving average
            smoothed_x = alpha * prev_x + (1.0 - alpha) * wx
            smoothed_y = alpha * prev_y + (1.0 - alpha) * wy

        self.gaze_xy = (smoothed_x, smoothed_y) #set new gaze pos
        self.write_gaze_for_cpp() #write to text file

        #returns tracker object
        return self

    #helper funciton to write the gaze positions to text file for world to read
    def write_gaze_for_cpp(self) -> None:
        GAZE_FILE.write_text(
            f"normalized-Eye-Gaze-positions: x:{self.gaze_xy[0]:.6f} "
            f"y:{self.gaze_xy[1]:.6f}\n",
            encoding="utf-8",
        )
