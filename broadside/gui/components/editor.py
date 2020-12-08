from PySide2.QtCore import QObject, Signal

from ..models.project import ProjectModel


class Editor(QObject):
    name = ""

    isValidChanged = Signal()
    dataChanged = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._isValid: bool = False

        self.view = None

    @property
    def isValid(self) -> bool:
        return self._isValid

    @isValid.setter
    def isValid(self, val: bool) -> None:
        if self.isValid is not val:
            self._isValid = val
            self.isValidChanged.emit()

    def beforeDelete(self) -> None:
        pass

    def validate(self) -> None:
        pass
