from os.path import dirname, realpath, join, isfile

from PySide2.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
)

from broadside.gui.components.mainwindow import MainWindow

CURRENT_DIR = dirname(realpath(__file__))


def get_styles_path() -> str:
    return join(CURRENT_DIR, "styles")


class Viewer:
    def __init__(self, *, app: QApplication):
        self.window = MainWindow()

        self.window.aboutAction.triggered.connect(lambda: self.showAbout())

        # self.sequence = SequenceModel(labels)
        # self.project = ProjectModel()

        # app.aboutToQuit()

        self.setStyleSheet()

    def showAbout(self):
        text = QLabel()
        text.setText("Digital pathology for local <i>in vivo</i> drug delivery.")

        layout = QHBoxLayout()
        layout.addWidget(text)

        dialog = QDialog(parent=self.window)
        dialog.setLayout(layout)
        dialog.setWindowTitle("About Broadside")

        dialog.exec_()

    def setStyleSheet(self, style: str = "default") -> None:
        filepath = join(get_styles_path(), f"{style}.qss")

        if not isfile(filepath):
            filepath = join(get_styles_path(), "default.qss")

        with open(filepath, "r") as file:
            self.window.setStyleSheet(file.read())

    def show(self):
        self.window.show()
