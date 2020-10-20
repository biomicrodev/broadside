import sys

from PySide2.QtWidgets import QApplication, QMainWindow


def run():
    app = QApplication()

    mw = QMainWindow(parent=None)
    mw.show()

    sys.exit(app.exec_())
