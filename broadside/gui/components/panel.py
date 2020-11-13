from PySide2.QtCore import QObject, Signal
from PySide2.QtWidgets import QWidget


class BasePanel(QObject):
    name = ""

    isReadyChanged = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._isReady: bool = False
        self.view: QWidget = QWidget()

    @property
    def isReady(self) -> bool:
        return self._isReady

    @isReady.setter
    def isReady(self, val: bool) -> None:
        if self.isReady is not val:
            self._isReady = val
            self.isReadyChanged.emit()
