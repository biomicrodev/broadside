from enum import Enum
from typing import Optional, List, Any, Dict

from broadside.gui.models.formulation import Formulation


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


class Device:
    def __init__(
        self,
        *,
        name: Optional[str] = "",
        longitudinalOrientation: Optional[LongitudinalOrientation] = None,
        longitudinalDirection: Optional[LongitudinalDirection] = None,
        angularDirection: Optional[AngularDirection] = None,
        payload: Optional[List[Formulation]] = None,
    ):
        self._name = name
        self._longitudinalOrientation = longitudinalOrientation
        self._longitudinalDirection = longitudinalDirection
        self._angularDirection = angularDirection
        self._payload = payload or []

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, val: str) -> None:
        self._name = val

    @property
    def longitudinalOrientation(self) -> Optional[LongitudinalOrientation]:
        return self._longitudinalOrientation

    @longitudinalOrientation.setter
    def longitudinalOrientation(self, val: LongitudinalOrientation) -> None:
        self._longitudinalOrientation = val

    @property
    def longitudinalDirection(self) -> Optional[LongitudinalDirection]:
        return self._longitudinalDirection

    @longitudinalDirection.setter
    def longitudinalDirection(self, val: LongitudinalDirection) -> None:
        self._longitudinalDirection = val

    @property
    def angularDirection(self) -> Optional[AngularDirection]:
        return self._angularDirection

    @angularDirection.setter
    def angularDirection(self, val: AngularDirection) -> None:
        self._angularDirection = val

    @property
    def payload(self) -> List:
        return self._payload

    @payload.setter
    def payload(self, val: List[Formulation]) -> None:
        self._payload = val

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "longitudinalOrientation": self.longitudinalOrientation,
            "longitudinalDirection": self.longitudinalDirection,
            "angularDirection": self.angularDirection,
            "payload": self.payload,
        }
