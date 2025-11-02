class CircleSmooth:

    # This smoothing algorthim works by starting with an inital gaze position 
    # and drawing a circle around it.

    # When a new value is passed to the update function,
    # it will be checked to see if it is inside the circle. If it is, then the center of the circle
    # is returned. This helps minimize some of the jitter from the eye tracker as it measures the gaze
    # in chuncks.

    # If the gaze position is outside the circle, then the circle's center will move toward the new postition
    # at some rate. The center of the circle is the only value returned, so it can accuratly filter out the
    # jitters.

    def __init__(self):
        self.center = None
        # Radius of the smoothing circle in the eye box units.
        self.RADIUS = 0.12
        # The rate at which the center moves to the next center spot
        # measured in percentage. So, the circle travels a certain percent
        # to the new center spot each update.
        self.INTERPOLATION_RATE = 0.1

    # Checks if the current gaze_xy point is inside the circle.
    def isInsideCircle(self, xy):
        distance = (xy[0]-self.center[0])**2 + (xy[1]-self.center[1])**2
        if distance > self.RADIUS**2:
            return False
        else:
            return True
        

    # Input to update() should be a tuple with x and y values between
    # (-1, -1) and (1, 1). The center is at (0, 0).
    # This function takes a gaxy_xy input and smooths out some of the jitteriness.
    def update(self, xy):
        # Edge Cases
        if xy is None:
            return self.center
        if self.center is None:
            self.center = (float(xy[0]), float(xy[1]))
            return self.center
        

        if self.isInsideCircle(xy):
            return self.center
        else:
            # This is the linear interpolation that lets the circle move towards
            # the new gaze position instead of instantly jumping to it.
            x = self.center[0]+(xy[0]-self.center[0])*self.INTERPOLATION_RATE
            y = self.center[1]+(xy[1]-self.center[1])*self.INTERPOLATION_RATE
            self.center = (x, y)
            return self.center