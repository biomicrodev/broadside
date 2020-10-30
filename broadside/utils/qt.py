from PySide2 import QtCore, QtUiTools
from PySide2.QtCore import QIODevice
from PySide2.QtWidgets import QWidget


def load_ui(filename: str, parent=None) -> QWidget:
    file = QtCore.QFile()
    file.setFileName(filename)
    file.setOpenMode(QIODevice.ReadOnly)

    loader = QtUiTools.QUiLoader(parent)
    widget = loader.load(file, parent)
    return widget
