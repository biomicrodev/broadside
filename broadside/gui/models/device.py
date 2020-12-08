from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any

from . import Serializable
from .formulation import Formulation


class Fiducial(Enum):
    Notch = "notch"


class LongitudinalOrientation(Enum):
    TipIntoPage = "tip into page/booster out of page"
    TipOutOfPage = "tip out of page/booster into page"


class LongitudinalDirection(Enum):
    IncreasingTowardsTip = "levels increasing towards tip"
    IncreasingTowardsBooster = "levels increasing towards booster"


class AngularDirection(Enum):
    Clockwise = "clockwise positive"
    CounterClockwise = "counterclockwise positive"


@dataclass
class Device(Serializable):
    name: str
    longitudinalOrientation: LongitudinalOrientation
    longitudinalDirection: LongitudinalDirection
    angularDirection: AngularDirection
    payload: List[Formulation]

    def __post_init__(self):
        self.payload = self.payload or []

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "longitudinal_orientation": self.longitudinalOrientation.value,
            "longitudinal_direction": self.longitudinalDirection.value,
            "angular_direction": self.angularDirection.value,
            "payload": [f.as_dict() for f in self.payload],
        }

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]):
        name = dct.get("name", "Unnamed")

        longOrient = dct.get("longitudinal_orientation", None)
        longOrient = (
            LongitudinalOrientation(longOrient) if longOrient is not None else None
        )

        longDir = dct.get("longitudinal_direction", None)
        longDir = LongitudinalDirection(longDir) if longDir is not None else None

        angDir = dct.get("angular_direction", None)
        angDir = AngularDirection(angDir) if angDir is not None else None

        payload = dct.get("payload", [])
        payload = [Formulation.from_dict(f) for f in payload]

        return cls(
            name=name,
            longitudinalOrientation=longOrient,
            longitudinalDirection=longDir,
            angularDirection=angDir,
            payload=payload,
        )
