from PySide2.QtCore import Qt
from PySide2.QtGui import QFontMetrics
from PySide2.QtWidgets import QFrame, QLabel, QMessageBox, QWidget


class QHLine(QFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setFixedHeight(1)
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Plain)


class QElidedLabel(QLabel):
    def setText(self, text: str) -> None:
        metrics = QFontMetrics(self.font())
        elidedText: str = metrics.elidedText(text, Qt.ElideMiddle, self.width())
        super().setText(elidedText)


def showSaveDialog(
    parent: QWidget = None, *, title: str, text: str
) -> QMessageBox.StandardButton:
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setWindowModality(Qt.ApplicationModal)
    box.setText(text)
    box.setIcon(QMessageBox.Question)
    box.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
    box.setDefaultButton(QMessageBox.Cancel)
    return box.exec_()


def showYesNoDialog(
    parent: QWidget = None, *, title: str, text: str
) -> QMessageBox.StandardButton:
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setWindowModality(Qt.ApplicationModal)
    box.setText(text)
    box.setIcon(QMessageBox.Question)
    box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    box.setDefaultButton(QMessageBox.No)
    return box.exec_()
