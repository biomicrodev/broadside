from dataclasses import dataclass, field
from typing import Dict, Any, List

from .device import NO_DEVICE
from .serializable import Serializable
from .utils import PointI, Angle


class Vector:
    def __init__(self, *, pos: PointI = PointI(), angle: float = 0.0):
        self._pos = pos
        self._angle = Angle(deg=angle)

    @property
    def pos(self) -> PointI:
        return self._pos

    @pos.setter
    def pos(self, val: PointI) -> None:
        self._pos.x = val.x
        self._pos.y = val.y

    @property
    def angle(self) -> float:
        return self._angle.deg

    @angle.setter
    def angle(self, val: float) -> None:
        self._angle.deg = val

    def is_valid(self) -> bool:
        return self.pos.is_valid()

    def as_dict(self) -> Dict[str, Any]:
        return {
            "pos": (self.pos.x, self.pos.y),
            "angle": self._angle.int,  # human-readable
        }

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]) -> "Vector":
        pos = dct.get("pos", None)
        pos = PointI(*(pos[:2])) if (pos is not None) else PointI()

        angle = dct.get("angle", 0.0)
        angle = float(angle)

        return cls(pos=pos, angle=angle)

    def __repr__(self) -> str:
        return f"Vector(pos={self.pos}, angle={self.angle})"


@dataclass
class Sample(Serializable):
    name: str = ""
    device_name: str = ""
    cohorts: Dict[str, str] = field(default_factory=dict)
    vector: Vector = field(default_factory=Vector)

    keys = ["name", "device_name"]
    headers = ["Name", "Device"]
    types = [str, str]

    def is_valid(self) -> bool:
        return (self.name != "") and (self.device_name != "") and self.vector.is_valid()

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "device_name": self.device_name,
            "cohorts": self.cohorts,
            "vector": self.vector.as_dict(),
        }

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]) -> "Sample":
        name = dct.get("name", "")

        device_name = dct.get("device_name", NO_DEVICE)

        cohorts = dct.get("cohorts", {})

        vector = dct.get("vector", {})
        vector = Vector.from_dict(vector)

        return cls(name=name, device_name=device_name, cohorts=cohorts, vector=vector)


@dataclass
class Block(Serializable):
    name: str = ""
    samples: List[Sample] = field(default_factory=list)

    def is_valid(self) -> bool:
        return (
            (self.name is not None)
            and (self.name != "")
            and all(s.is_valid() for s in self.samples)
        )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "samples": [s.as_dict() for s in self.samples],
        }

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]):
        name = dct.get("name", "")

        samples = dct.get("samples", [])
        samples = [Sample.from_dict(s) for s in samples]

        return cls(name=name, samples=samples)
