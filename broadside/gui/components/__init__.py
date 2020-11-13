# from PySide2.QtWidgets import QWidget
# from napari._qt.qt_viewer import QtViewer
# from napari.components import ViewerModel

from .analysis import AnalysisPanel
from .annotation import AnnotationPanel
from .mainwindow import MainWindow
from .panel import BasePanel
from .project import ProjectPanel

__all__ = [
    "AnalysisPanel",
    "AnnotationPanel",
    "ProjectPanel",
    "BasePanel",
    "MainWindow",
]


# def create_napari_viewer() -> QWidget:
#     viewer = ViewerModel()
#     viewer.theme = "light"
#
#     qt_viewer = QtViewer(viewer)
#
#     return qt_viewer
