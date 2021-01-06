import math

twopi = math.pi * 2


class PointF:
    def __init__(self, /, x: float, y: float):
        self.x = x
        self.y = y

    @property
    def x(self) -> float:
        return self._x

    @x.setter
    def x(self, val: float) -> None:
        self._x = float(val)

    @property
    def y(self) -> float:
        return self._y

    @y.setter
    def y(self, val: float) -> None:
        self._y = float(val)


class PointI:
    def __init__(self, /, x: int = None, y: int = None):
        self.x = x
        self.y = y

    @property
    def x(self) -> int:
        return self._x

    @x.setter
    def x(self, val: int) -> None:
        self._x = int(val) if val is not None else None

    @property
    def y(self) -> int:
        return self._y

    @y.setter
    def y(self, val: int) -> None:
        self._y = int(val) if val is not None else None

    def is_valid(self) -> bool:
        return (self.x is not None) and (self.y is not None)


def clip_angle(val: float) -> float:
    val = math.fmod(val, twopi)
    if val < 0.0:
        val += twopi
    return val


class Angle:
    """
    Angle, [0, 2pi).
    On the view side, we use degrees; internally, we use radians.

    This is overkill.
    """

    def __init__(self, rad: float = None, deg: float = None):
        if rad is not None and deg is not None:
            raise RuntimeError("Cannot pass in both rad and deg")
        elif rad is None and deg is None:
            raise RuntimeError("Need to pass at least one of rad and deg")

        # radians internally
        elif rad is not None:
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
        # all setting goes through here
        self._val = clip_angle(val)

    @property
    def deg(self) -> float:
        return math.degrees(self._val)

    @deg.setter
    def deg(self, val: float) -> None:
        rad = math.radians(val)
        self.rad = rad

    @property
    def int(self) -> int:
        return int(round(self.deg))

    def __repr__(self) -> str:
        return f"Angle({self.rad})"

    def __add__(self, other: "Angle"):
        val1 = self.rad
        val2 = other.rad
        return Angle(rad=(val1 + val2))
