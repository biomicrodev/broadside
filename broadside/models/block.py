from dataclasses import dataclass
from typing import Dict, Any, List, Tuple, Optional

from .serializable import Serializable
from ..utils import norm_angle

Point2D = Tuple[float, float]


class Vector(Serializable):
    def __init__(self, *, pos: Point2D, angle: float):
        self._pos = pos
        self._angle = angle

    @property
    def pos(self) -> Optional[Point2D]:
        return self._pos

    @pos.setter
    def pos(self, val: Point2D) -> None:
        self._pos = val

    @property
    def angle(self) -> Optional[float]:
        return self._angle

    @angle.setter
    def angle(self, val: float) -> None:
        self._angle = norm_angle(val)

    def as_dict(self) -> Dict[str, Any]:
        return {"pos": self.pos, "angle": self.angle}

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]):
        pos = dct.get("pos", None)
        pos = tuple(pos) if pos is not None else None

        angle = dct.get("angle", None)
        angle = float(angle) if angle is not None else None

        return cls(pos=pos, angle=angle)


class Sample(Serializable):
    keys = ["name", "deviceName"]
    headers = ["Name", "Device name"]
    types = [str, str]

    def __init__(
        self, *, name: str = "", deviceName: str = "", cohorts: Dict[str, str] = None
    ):
        self._name = name
        self._deviceName = deviceName
        self._cohorts = cohorts or {}

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, val: str) -> None:
        self._name = val

    @property
    def deviceName(self) -> str:
        return self._deviceName

    @deviceName.setter
    def deviceName(self, val: str) -> None:
        self._deviceName = val

    @property
    def cohorts(self) -> Dict[str, str]:
        return self._cohorts

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "device_name": self.deviceName,
            "cohorts": self.cohorts,
        }

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]):
        name = dct.get("name", "")
        deviceName = dct.get("device_name", "")
        cohorts = dct.get("cohorts", {})

        return cls(name=name, deviceName=deviceName, cohorts=cohorts)


class SampleVector(Serializable):
    def __init__(self, *, sample: Sample, pos: Point2D, angle: float):
        self._sample = sample
        self._pos = pos
        self._angle = norm_angle(angle)

    @property
    def sample(self) -> Sample:
        return self._sample

    @sample.setter
    def sample(self, val: Sample) -> None:
        self._sample = val

    @property
    def pos(self) -> Point2D:
        return self._pos

    @pos.setter
    def pos(self, val: Point2D) -> None:
        self._pos = val

    @property
    def angle(self) -> float:
        return self._angle

    @angle.setter
    def angle(self, val: float) -> None:
        self._angle = norm_angle(val)


@dataclass
class Block(Serializable):
    name: str
    samples: List[Sample]
    vectors: List[Vector]

    # TODO: refactor samples into sample_vectors

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "samples": [s.as_dict() for s in self.samples],
            "vectors": [v.as_dict() for v in self.vectors],
        }

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]):
        name = dct.get("name", "Unnamed")

        samples = dct.get("samples", [])
        samples = [Sample.from_dict(s) for s in samples]

        vectors = dct.get("vectors", [])
        vectors = [Vector.from_dict(v) for v in vectors]
        if len(vectors) < len(samples):
            vectors.extend(
                [Vector.from_dict({}) for _ in range(len(samples) - len(vectors))]
            )

        return cls(name=name, samples=samples, vectors=vectors)
