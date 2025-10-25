from dataclasses import dataclass

@dataclass
class Vec2:
    x: float
    y: float

    def __iter__(self):
        yield self.x
        yield self.y

    def __repr__(self) -> str:
        return f"Vec2(x={self.x:.3f}, y={self.y:.3f})"
