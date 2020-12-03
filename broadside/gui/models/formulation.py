import math
from typing import Optional, Dict, Union, Any

from . import Serializable


class Formulation(Serializable):
    keys = ["level", "angle", "name"]
    headers = ["Level", "Angle", "Name"]
    types = [str, float, str]

    def __init__(
        self,
        *,
        level: Union[str, int] = "",
        angle: Optional[float] = None,
        name: str = ""
    ):
        self._level: str = str(level)
        self._angle: float = angle
        self._name: str = name

    @property
    def level(self) -> str:
        return self._level

    @level.setter
    def level(self, val: Union[str, int]) -> None:
        self._level = str(val)

    @property
    def angle(self) -> Optional[float]:
        return self._angle

    @angle.setter
    def angle(self, val: float) -> None:
        # in degrees!
        # `math.fmod` not guaranteed to return a positive value
        val = math.fmod(val, 360.0)
        if val < 0.0:
            val += 360.0
        self._angle = round(val)

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, val: str) -> None:
        self._name = val

    def isValid(self) -> bool:
        return (self.level != "") and (self.angle is not None) and (self.name != "")

    def as_dict(self) -> Dict[str, Any]:
        return {"level": self.level, "angle": self.angle, "name": self.name}

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]):
        """Serialization code. Awkward, but works (at least for now)"""
        return cls(level=dct["level"], angle=float(dct["angle"]), name=dct["name"])
