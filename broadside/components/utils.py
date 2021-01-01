from pathlib import Path
from typing import Optional

from PySide2.QtCore import Qt, QDir
from PySide2.QtGui import QFontMetrics
from PySide2.QtWidgets import QFrame, QLabel, QMessageBox, QWidget, QFileDialog


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
    box.setText(text)
    box.setWindowModality(Qt.ApplicationModal)
    box.setIcon(QMessageBox.Question)
    box.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
    box.setDefaultButton(QMessageBox.Cancel)
    return box.exec_()


def showYesNoDialog(
    parent: QWidget = None, *, title: str, text: str
) -> QMessageBox.StandardButton:
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(text)
    box.setWindowModality(Qt.ApplicationModal)
    box.setIcon(QMessageBox.Question)
    box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    box.setDefaultButton(QMessageBox.No)
    return box.exec_()


def showSelectProjectDialog(parent: QWidget = None) -> Optional[Path]:
    dialog = QFileDialog(parent, Qt.Dialog)
    dialog.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog)
    dialog.setAcceptMode(QFileDialog.AcceptSave)
    dialog.setLabelText(QFileDialog.LookIn, "Select project folder")
    dialog.setFileMode(QFileDialog.Directory)
    dialog.setOption(QFileDialog.ShowDirsOnly, True)
    dialog.setViewMode(QFileDialog.Detail)
    dialog.setDirectory(QDir.homePath())

    if dialog.exec_():
        paths = dialog.selectedFiles()
        assert len(paths) == 1
        path = Path(paths[0])
        return path

    return None


def updateStyle(w: QWidget) -> None:
    w.style().unpolish(w)
    w.style().polish(w)
