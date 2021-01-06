from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any

from .formulation import Formulation
from .serializable import Serializable


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
    name: str = ""
    longitudinal_orientation: LongitudinalOrientation = None
    longitudinal_direction: LongitudinalDirection = None
    angular_direction: AngularDirection = None
    payload: List[Formulation] = field(default_factory=list)

    def is_formulations_unique(self) -> bool:
        levels_angles = [(f.level, f.angle) for f in self.payload]
        levels_angles_as_set = set(levels_angles)
        return len(levels_angles) == len(levels_angles_as_set)

    def is_valid(self) -> bool:
        return (
            (self.name != "")
            and (self.longitudinal_orientation is not None)
            and (self.longitudinal_direction is not None)
            and (self.angular_direction is not None)
            and all(f.is_valid() for f in self.payload)
            and self.is_formulations_unique()
        )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "longitudinal_orientation": self.longitudinal_orientation.value,
            "longitudinal_direction": self.longitudinal_direction.value,
            "angular_direction": self.angular_direction.value,
            "payload": [f.as_dict() for f in self.payload],
        }

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]):
        name = dct.get("name", "Unnamed")

        long_orient = dct.get("longitudinal_orientation", None)
        long_orient = (
            LongitudinalOrientation(long_orient) if long_orient is not None else None
        )

        long_dir = dct.get("longitudinal_direction", None)
        long_dir = LongitudinalDirection(long_dir) if long_dir is not None else None

        ang_dir = dct.get("angular_direction", None)
        ang_dir = AngularDirection(ang_dir) if ang_dir is not None else None

        payload = dct.get("payload", [])
        payload = [Formulation.from_dict(f) for f in payload]

        return cls(
            name=name,
            longitudinal_orientation=long_orient,
            longitudinal_direction=long_dir,
            angular_direction=ang_dir,
            payload=payload,
        )
