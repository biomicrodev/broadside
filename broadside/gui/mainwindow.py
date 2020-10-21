from PySide2.QtWidgets import QMainWindow
from napari._qt.qt_viewer import QtViewer
from napari.components import ViewerModel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(parent=None)

        viewer = ViewerModel()
        viewer.theme = "light"
        qtViewer = QtViewer(viewer)

        self.setCentralWidget(qtViewer)

        self.setWindowTitle("Broadside")
        self.setMinimumWidth(300)
        self.setMinimumHeight(300)
