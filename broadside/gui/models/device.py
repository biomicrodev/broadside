from enum import Enum
from typing import List, Optional, Dict, Any

from PySide2.QtCore import QObject, QAbstractListModel

from broadside.gui.models import QStaleableObject


class DeviceOrientation(Enum):
    TipIntoScreen = "tip into screen/booster out of screen"
    TipOutOfScreen = "tip out of screen/booster into screen"


class DeviceDirectionality(Enum):
    Clockwise = "clockwise positive"
    Counterclockwise = "counterclockwise positive"


class Payload(QAbstractListModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Device(QStaleableObject):
    def __init__(
        self,
        *,
        name: Optional[str] = "",
        orientation: Optional[DeviceOrientation] = None,
        directionality: Optional[DeviceDirectionality] = None,
        payload: Optional[List] = None,
        fiducial: Optional[str] = "",
        parent: Optional[QObject] = None
    ):
        super().__init__(parent=parent)

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
        if self.name != val:
            self._name = val
            self.isStale = True

    @property
    def orientation(self) -> DeviceOrientation:
        return self._orientation

    @orientation.setter
    def orientation(self, val: DeviceOrientation):
        if self.orientation != val:
            self._orientation = val
            self.isStale = True

    @property
    def directionality(self) -> DeviceDirectionality:
        return self._directionality

    @directionality.setter
    def directionality(self, val: DeviceDirectionality) -> None:
        if self.directionality != val:
            self._directionality = val
            self.isStale = True

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "orientation": self.orientation,
            "directionality": self.directionality,
            "payload": self.payload,
            "fiducial": self.fiducial,
        }


if __name__ == "__main__":
    device = Device()
