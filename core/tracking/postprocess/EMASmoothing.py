class EMA:
    def __init__(self, alpha: float = 0.35):
        self.alpha = float(alpha)
        self._xy = None

    def update(self, xy):
        if xy is None:
            return self._xy
        if self._xy is None:
            self._xy = (float(xy[0]), float(xy[1]))
            return self._xy
        a = self.alpha
        self._xy = (a*xy[0] + (1-a)*self._xy[0], a*xy[1] + (1-a)*self._xy[1])
        return self._xy
