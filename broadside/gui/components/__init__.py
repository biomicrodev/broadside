from PySide2.QtWidgets import QWidget
from napari._qt.qt_viewer import QtViewer
from napari.components import ViewerModel


def create_napari_viewer() -> QWidget:
    viewer = ViewerModel()
    viewer.theme = "light"

    qt_viewer = QtViewer(viewer)

    return qt_viewer
