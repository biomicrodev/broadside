import math
from typing import Tuple, Optional


class PointF:
    def __init__(self, /, x: Optional[float] = None, y: Optional[float] = None):
        self._x = x
        self._y = y

    @property
    def x(self) -> Optional[float]:
        return self._x

    @x.setter
    def x(self, val: Optional[float]) -> None:
        new_val = float(val) if val is not None else None
        if self.x != new_val:
            self._x = new_val

    @property
    def y(self) -> Optional[float]:
        return self._y

    @y.setter
    def y(self, val: Optional[float]) -> None:
        new_val = float(val) if val is not None else None
        if self.y != new_val:
            self._y = new_val

    def is_valid(self) -> bool:
        return (self.x is not None) and (self.y is not None)

    def __repr__(self) -> str:
        return f"PointF(x={self.x}, y={self.y})"

    def as_tuple(self) -> Tuple[Optional[float], Optional[float]]:
        return (self.x, self.y)


def clip_angle(val: float) -> float:
    val = math.fmod(val, (math.pi * 2))
    if val < 0.0:
        val += math.pi * 2
    return val


class Angle:
    """
    Angle, [0, 2pi)
    """

    def __init__(self, rad: Optional[float] = None, deg: Optional[float] = None):
        if rad is not None and deg is not None:
            raise RuntimeError("Cannot pass in both rad and deg")
        elif rad is None and deg is None:
            raise RuntimeError("Need to pass at least one of rad and deg")

        # radians internally
        if rad is not None:
            self.rad = rad
        elif deg is not None:
            self.deg = deg

    @classmethod
    def from_rad(cls, val: float) -> "Angle":
        return cls(val)

    @classmethod
    def from_deg(cls, val: float) -> "Angle":
        val = math.radians(val)
        return cls(val)

    @property
    def rad(self) -> float:
        return self._val

    @rad.setter
    def rad(self, val: float) -> None:
        # all angle-setting goes through here
        self._val = clip_angle(val)

    @property
    def deg(self) -> float:
        return math.degrees(self._val)

    @deg.setter
    def deg(self, val: float) -> None:
        self.rad = math.radians(val)

    @property
    def int(self) -> int:
        return int(round(self.deg))

    def __repr__(self) -> str:
        return f"Angle({self.rad})"

    def __add__(self, other: "Angle") -> "Angle":
        return Angle(rad=self.rad + other.rad)

    def __sub__(self, other: "Angle") -> "Angle":
        return Angle(rad=self.rad - other.rad)

    def __iadd__(self, other: "Angle") -> "Angle":
        self.rad += other.rad
        return self

    def __isub__(self, other: "Angle") -> "Angle":
        self.rad -= other.rad
        return self
