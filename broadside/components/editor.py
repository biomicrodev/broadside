from typing import Optional

from qtpy.QtCore import QObject, Signal
from qtpy.QtWidgets import QWidget


class Editor(QObject):
    name = ""

    dataChanged = Signal()
    isValidChanged = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._isValid: bool = False
        self.view: Optional[QWidget] = None

    @property
    def isValid(self) -> bool:
        return self._isValid

    @isValid.setter
    def isValid(self, val: bool) -> None:
        if self.isValid is not val:
            self._isValid = val
            self.isValidChanged.emit()

    def validate(self) -> None:
        pass

    def refresh(self) -> None:
        pass
