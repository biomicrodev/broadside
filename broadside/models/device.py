from enum import Enum
from typing import List, Optional


class DeviceOrientation(Enum):
    TipIntoScreen = "tip into screen/booster out of screen"
    TipOutOfScreen = "tip out of screen/booster into screen"


class DeviceDirectionality(Enum):
    Clockwise = "clockwise positive"
    Counterclockwise = "counterclockwise positive"


class Device:
    def __init__(
        self,
        *,
        name: Optional[str] = "",
        orientation: Optional[DeviceOrientation] = None,
        directionality: Optional[DeviceDirectionality] = None,
        payload: Optional[List] = None,
        fiducial: Optional[str] = ""
    ):
        self._name = name
        self._orientation = orientation
        self._directionality = directionality
        self._payload = payload or []
        self._fiducial = fiducial

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, val: str) -> None:
        self._name = val

    @property
    def orientation(self) -> Optional[DeviceOrientation]:
        return self._orientation

    @orientation.setter
    def orientation(self, val: DeviceOrientation) -> None:
        self._orientation = val

    @property
    def directionality(self) -> Optional[DeviceDirectionality]:
        return self._directionality

    @directionality.setter
    def directionality(self, val: DeviceDirectionality) -> None:
        self._directionality = val

    # FIXME: manage payload later

    @property
    def fiducial(self) -> Optional[str]:
        return self._fiducial

    @fiducial.setter
    def fiducial(self, val: str) -> None:
        self._fiducial = val
