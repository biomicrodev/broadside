from os.path import dirname, realpath, join, isfile

from PySide2.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
)

from broadside.gui.components.MainWindow import MainWindow
from broadside.gui.components.ProjectWidget import ProjectWidget
from broadside.models.sequence import SequenceModel

CURRENT_DIR = dirname(realpath(__file__))


def get_styles_path() -> str:
    return join(CURRENT_DIR, "styles")


class Viewer:
    def __init__(self, *, app: QApplication):
        self.window = MainWindow()

        self.sequence = SequenceModel(5)
        # self.sequence.events.index.connect(lambda event: print(event.index))
        self.window.setCentralWidget(ProjectWidget(parent=self.window))

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
