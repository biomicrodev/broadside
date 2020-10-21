import sys

from PySide2.QtWidgets import QApplication

from broadside.gui.mainwindow import MainWindow


def run():
    app = QApplication()

    mw = MainWindow()
    mw.show()

    sys.exit(app.exec_())
