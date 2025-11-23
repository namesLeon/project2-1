from pathlib import Path

from core.tracking.utils import draw

log_fp = open(Path("gaze_out.txt"), "w", buffering=1)


class MediaPipeEyeTracker():
    """
    Eye tracker which implements Google's MediaPipe FaceMesh that tracks only your left eye.
    """

    # eyetracker constructor
    def __init__(self):
        self.gaze_xy = (0, 0)



    def process(self, frame, faceMesh):
        results = faceMesh.process(frame)

        if results.multi_face_landmarks:
            for landmarks in results.multi_face_landmarks:
                leftIris = landmarks.landmark[468]

                draw.drawFaceMesh(frame, landmarks)
                draw.drawIris(frame, leftIris)

                # Mediapipe already normalizes the position of the iris from [0, 1]
                self.gaze_xy = leftIris.x, leftIris.y
                self.write_gaze_for_cpp()



    def write_gaze_for_cpp(self):
        Path("gaze_out.txt").write_text(
            f"normalized-Eye-Gaze-positions: x:{self.gaze_xy[0]:.6f} y:{self.gaze_xy[1]:.6f}\n",
            encoding="utf-8",
        )