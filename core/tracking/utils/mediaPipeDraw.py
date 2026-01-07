import cv2


class MediaPipeDraw:

    def __init__(self):
        self.drawn = False


    def toggleGazeVisuals(self):
        # Remove the visuals if they are displayed.
        if self.drawn:
            # Visuals are removed on the next frame as the camera frame draws
            # over the previous frame.
            self.drawn = False

        # Add the visuals if they are not displayed.
        else:
            self.drawn = True


    def drawGaze(self, frame_bgr, pxy):
        if self.drawn:
            cv2.circle(frame_bgr, pxy, 10, (0, 255, 0), 2)



    def drawFPS(self, frame_bgr, fps):
        if self.drawn:
            cv2.putText(
                frame_bgr,
                f"FPS: {fps:.1f}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 255, 255),
                2,
                cv2.LINE_AA,
            )