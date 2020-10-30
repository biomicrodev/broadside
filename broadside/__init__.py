import sys

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication

from broadside.gui.viewer import Viewer


def run():
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)

    app = QApplication()

    viewer = Viewer(app=app)
    viewer.show()

    sys.exit(app.exec_())
