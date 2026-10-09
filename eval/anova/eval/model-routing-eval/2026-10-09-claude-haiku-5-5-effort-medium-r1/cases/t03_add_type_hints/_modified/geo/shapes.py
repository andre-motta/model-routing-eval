from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

Point = tuple[float, float]


def distance(a: Point, b: Point) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def perimeter(points: Sequence[Point]) -> float:
    if len(points) < 2:
        return 0.0
    return sum(distance(points[i], points[(i + 1) % len(points)]) for i in range(len(points)))


def centroid(points: Sequence[Point]) -> Point | None:
    if not points:
        return None
    n = len(points)
    return (sum(p[0] for p in points) / n, sum(p[1] for p in points) / n)


class Polygon:
    def __init__(self, points: Iterable[Point], name: str | None = None) -> None:
        self.points: list[Point] = list(points)
        self.name: str | None = name

    def area(self) -> float:
        s = 0.0
        for i, (x1, y1) in enumerate(self.points):
            x2, y2 = self.points[(i + 1) % len(self.points)]
            s += x1 * y2 - x2 * y1
        return abs(s) / 2

    def scaled(self, factor: float) -> Polygon:
        return Polygon([(x * factor, y * factor) for x, y in self.points], self.name)

    def describe(self) -> dict[str, str | int | float | None]:
        return {"name": self.name, "sides": len(self.points), "area": self.area()}
