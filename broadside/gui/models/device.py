from enum import Enum
from typing import Optional, List, Union, Any, Dict

from broadside.gui.models.formulation import Formulation


class Fiducial(Enum):
    Notch = "notch"


class LongitudinalDirection(Enum):
    TipIntoScreen = "tip into screen/booster out of screen"
    TipOutOfScreen = "tip out of screen/booster into screen"


class LongitudinalOrdinality(Enum):
    IncreasingTowardsTip = "levels increasing towards tip"
    IncreasingTowardsBooster = "levels increasing towards booster"


class AngularDirection(Enum):
    Clockwise = "clockwise positive"
    Counterclockwise = "counterclockwise positive"


class Device:
    def __init__(
        self,
        *,
        name: Optional[str] = "",
        longitudinalDirection: Optional[LongitudinalDirection] = None,
        longitudinalOrdinality: Optional[LongitudinalOrdinality] = None,
        angularDirection: Optional[AngularDirection] = None,
        payload: Optional[List[Formulation]] = None,
        fiducial: Optional[Union[str, Fiducial]] = "",
    ):
        self._name = name
        self._longitudinalDirection = longitudinalDirection
        self._longitudinalOrdinality = longitudinalOrdinality
        self._angularDirection = angularDirection
        self._payload = payload or []
        self._fiducial = fiducial

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, val: str) -> None:
        self._name = val

    @property
    def longitudinalDirection(self) -> Optional[LongitudinalDirection]:
        return self._longitudinalDirection

    @longitudinalDirection.setter
    def longitudinalDirection(self, val: LongitudinalDirection) -> None:
        self._longitudinalDirection = val

    @property
    def longitudinalOrdinality(self) -> Optional[LongitudinalOrdinality]:
        return self._longitudinalOrdinality

    @longitudinalOrdinality.setter
    def longitudinalOrdinality(self, val: LongitudinalOrdinality) -> None:
        self._longitudinalOrdinality = val

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

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "longitudinalDirection": self.longitudinalOrdinality,
            "longitudinalOrdinality": self.longitudinalOrdinality,
            "angularDirection": self.angularDirection,
            "payload": self.payload,
        }
