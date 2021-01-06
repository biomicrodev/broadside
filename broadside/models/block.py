from dataclasses import dataclass, field
from typing import Dict, Any, List

from .serializable import Serializable
from ..utils import clip_angle


class Vector:
    def __init__(self, *, pos: List[int] = None, angle: float = 0.0):
        self.pos = pos or [None, None]
        assert len(self.pos) == 2
        self.angle = angle

    @property
    def angle(self) -> float:
        return self._angle

    @angle.setter
    def angle(self, val: float) -> None:
        self._angle = clip_angle(val)

    def is_valid(self) -> bool:
        return (self.pos[0] is not None) and (self.pos[1] is not None)

    def as_dict(self) -> Dict[str, Any]:
        return {"pos": self.pos, "angle": self.angle}

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]) -> "Vector":
        pos = dct.get("pos", [None, None])

        angle = dct.get("angle", 0.0)
        angle = float(angle)

        return cls(pos=pos, angle=angle)


@dataclass
class Sample(Serializable):
    name: str = ""
    device_name: str = ""
    cohorts: Dict[str, str] = field(default_factory=dict)
    vector: Vector = field(default_factory=Vector)

    keys = ["name", "device_name"]
    headers = ["Name", "Device name"]
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

        device_name = dct.get("device_name", "")

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
