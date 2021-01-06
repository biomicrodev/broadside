from typing import Dict, Any

from .serializable import Serializable
from .utils import Angle


class Formulation(Serializable):
    keys = ["level", "angle", "name"]
    headers = ["Level", "Angle", "Name"]
    types = [str, float, str]

    def __init__(self, *, level: str = "", angle: float = 0.0, name: str = ""):
        self.level = level
        self._angle = Angle(deg=angle)
        self.name = name

    @property
    def angle(self) -> float:
        return self._angle.deg

    @angle.setter
    def angle(self, val: float) -> None:
        self._angle.deg = val

    def is_valid(self) -> bool:
        return (self.level != "") and (self.name != "")

    def as_dict(self) -> Dict[str, Any]:
        return {"level": self.level, "angle": self._angle.int, "name": self.name}

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]) -> "Formulation":
        level = dct.get("level", "")

        angle = dct.get("angle", 0.0)
        angle = float(angle)

        name = dct.get("name", "")

        return cls(level=level, angle=angle, name=name)
