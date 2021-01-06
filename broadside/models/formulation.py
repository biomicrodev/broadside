from dataclasses import dataclass, field
from typing import Optional, Dict, Union, Any

from .serializable import Serializable
from ..utils import clip_angle


class Formulation(Serializable):
    keys = ["level", "angle", "name"]
    headers = ["Level", "Angle", "Name"]
    types = [str, float, str]

    def __init__(self, *, level: str = "", angle: float = 0.0, name: str = ""):
        self.level = level
        self.angle = angle
        self.name = name

    @property
    def angle(self) -> float:
        return self._angle

    @angle.setter
    def angle(self, val: float) -> None:
        self._angle = clip_angle(val)

    def is_valid(self) -> bool:
        return (self.level != "") and (self.name != "")

    def as_dict(self) -> Dict[str, Any]:
        return {"level": self.level, "angle": self.angle, "name": self.name}

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]) -> "Formulation":
        level = dct.get("level", "")

        angle = dct.get("angle", 0.0)
        angle = float(angle)

        name = dct.get("name", "")

        return cls(level=level, angle=angle, name=name)
