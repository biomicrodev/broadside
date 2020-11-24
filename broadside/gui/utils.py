from PySide2.QtCore import Qt, QObject, Signal
from PySide2.QtGui import QFontMetrics
from PySide2.QtWidgets import QFrame, QLabel, QMessageBox


class QStaleableObject(QObject):
    """
    A simple QObject that indicates whether it is stale or not. To use this object,
    connect to the `isStaleChanged` signal and set `isStale` appropriately.
    """

    isStaleChanged = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._isStale = False

    @property
    def isStale(self) -> bool:
        return self._isStale

    @isStale.setter
    def isStale(self, val: bool) -> None:
        if self.isStale is not val:
            self._isStale = val
            self.isStaleChanged.emit()


class QHLine(QFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Plain)


class QElidedLabel(QLabel):
    def setText(self, text: str):
        metrics = QFontMetrics(self.font())
        elidedText: str = metrics.elidedText(text, Qt.ElideMiddle, self.width())
        super().setText(elidedText)


def showSaveDialog(*, title: str, text: str) -> QMessageBox.StandardButton:
    box = QMessageBox()
    box.setWindowTitle(title)
    box.setWindowModality(Qt.ApplicationModal)
    box.setText(text)
    box.setIcon(QMessageBox.Question)
    box.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
    box.setDefaultButton(QMessageBox.Cancel)
    return box.exec_()


def showDeleteDialog(*, title: str, text: str) -> QMessageBox.StandardButton:
    box = QMessageBox()
    box.setWindowTitle(title)
    box.setWindowModality(Qt.ApplicationModal)
    box.setText(text)
    box.setIcon(QMessageBox.Question)
    box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    box.setDefaultButton(QMessageBox.No)
    return box.exec_()
