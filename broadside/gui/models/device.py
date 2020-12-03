from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict, Any

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


# class Device(Serializable):
#     def __init__(
#         self,
#         *,
#         name: Optional[str] = "",
#         longitudinalOrientation: Optional[LongitudinalOrientation] = None,
#         longitudinalDirection: Optional[LongitudinalDirection] = None,
#         angularDirection: Optional[AngularDirection] = None,
#         payload: Optional[List[Formulation]] = None,
#     ):
#         self._name: str = name
#         self._longitudinalOrientation: LongitudinalOrientation = longitudinalOrientation
#         self._longitudinalDirection: LongitudinalDirection = longitudinalDirection
#         self._angularDirection: AngularDirection = angularDirection
#         self._payload: List[Formulation] = payload or []
#
#     @property
#     def name(self) -> str:
#         return self._name
#
#     @name.setter
#     def name(self, val: str) -> None:
#         self._name = val
#
#     @property
#     def longitudinalOrientation(self) -> Optional[LongitudinalOrientation]:
#         return self._longitudinalOrientation
#
#     @longitudinalOrientation.setter
#     def longitudinalOrientation(self, val: LongitudinalOrientation) -> None:
#         self._longitudinalOrientation = val
#
#     @property
#     def longitudinalDirection(self) -> Optional[LongitudinalDirection]:
#         return self._longitudinalDirection
#
#     @longitudinalDirection.setter
#     def longitudinalDirection(self, val: LongitudinalDirection) -> None:
#         self._longitudinalDirection = val
#
#     @property
#     def angularDirection(self) -> Optional[AngularDirection]:
#         return self._angularDirection
#
#     @angularDirection.setter
#     def angularDirection(self, val: AngularDirection) -> None:
#         self._angularDirection = val
#
#     @property
#     def payload(self) -> List:
#         return self._payload
#
#     @payload.setter
#     def payload(self, val: List[Formulation]) -> None:
#         self._payload = val
#
#     def as_dict(self) -> Dict[str, Any]:
#         # we can't pass the enum raw, we'll have to pass the value corresponding to the
#         # enum (TODO: refactor this if there are many enums to be serialized)
#         return {
#             "name": self.name,
#             "longitudinalOrientation": self.longitudinalOrientation,
#             "longitudinalDirection": self.longitudinalDirection,
#             "angularDirection": self.angularDirection,
#             "payload": self.payload,
#         }
#
#     @classmethod
#     def from_dict(cls, dct: Dict[str, Any]):
#         return cls(
#             name=dct["name"],
#             longitudinalOrientation=LongitudinalOrientation(
#                 dct["longitudinalOrientation"]
#             ),
#             longitudinalDirection=LongitudinalDirection(dct["longitudinalDirection"]),
#             angularDirection=AngularDirection(dct["angularDirection"]),
#             payload=[Formulation.from_dict(f) for f in dct["formulation"]],
#         )


@dataclass
class Device(Serializable):
    name: Optional[str] = ""
    longitudinalOrientation: Optional[LongitudinalOrientation] = None
    longitudinalDirection: Optional[LongitudinalDirection] = None
    angularDirection: Optional[AngularDirection] = None
    payload: List[Formulation] = None

    def __post_init__(self):
        self.payload = self.payload or []

    def as_dict(self) -> Dict[str, Any]:
        # we can't pass the enum raw, we'll have to pass the value corresponding to the
        # enum (TODO: refactor this if there are many enums to be serialized)
        return {
            "name": self.name,
            "longitudinalOrientation": self.longitudinalOrientation.value,
            "longitudinalDirection": self.longitudinalDirection.value,
            "angularDirection": self.angularDirection.value,
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]):
        longOrient = (
            LongitudinalOrientation(dct["longitudinalOrientation"])
            if dct["longitudinalOrientation"]
            else None
        )

        longDir = (
            LongitudinalDirection(dct["longitudinalDirection"])
            if dct["longitudinalDirection"]
            else None
        )

        angDir = (
            AngularDirection(dct["angularDirection"])
            if dct["angularDirection"]
            else None
        )

        return cls(
            name=dct["name"],
            longitudinalOrientation=longOrient,
            longitudinalDirection=longDir,
            angularDirection=angDir,
            payload=[Formulation.from_dict(f) for f in dct["payload"]],
        )
