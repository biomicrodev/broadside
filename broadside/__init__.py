import sys

from PySide2.QtWidgets import QApplication

from broadside.gui.viewer import Viewer


def run():
    app = QApplication()

    viewer = Viewer(app=app)
    viewer.show()

    sys.exit(app.exec_())
