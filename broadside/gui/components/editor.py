from PySide2.QtCore import QObject, Signal

from ..models.project import ProjectModel


class BaseEditor(QObject):
    name = ""

    isCompleteChanged = Signal()
    dataChanged = Signal()

    def __init__(self, model: ProjectModel, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._isComplete: bool = False

        self.model = model
        self.view = None

    @property
    def isComplete(self) -> bool:
        return self._isComplete

    @isComplete.setter
    def isComplete(self, val: bool) -> None:
        if self.isComplete is not val:
            self._isComplete = val
            self.isCompleteChanged.emit()

    def beforeDelete(self) -> None:
        pass
