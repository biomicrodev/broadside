from os.path import dirname, realpath, join

from PySide2.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenuBar,
    QMenu,
    QAction,
    QDialog,
    QHBoxLayout,
    QLabel,
)


def get_styles_path() -> str:
    return join(dirname(realpath(__file__)), "styles")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(parent=None)

        self.setWindowStyleSheet("default")

        self.initMenuBar()

        self.setWindowTitle("Broadside")
        self.setMinimumWidth(500)
        self.setMinimumHeight(500)

    def setWindowStyleSheet(self, style: str) -> None:
        with open(join(get_styles_path(), f"{style}.qss"), "r") as file:
            self.setStyleSheet(file.read())

    def initMenuBar(self) -> None:
        menuBar = QMenuBar(parent=self)

        fileMenu = QMenu(parent=menuBar)
        fileMenu.setTitle("&File")
        menuBar.addMenu(fileMenu)

        helpMenu = QMenu(parent=menuBar)
        helpMenu.setTitle("&Help")
        aboutAction = QAction(text="About", parent=helpMenu)
        aboutAction.triggered.connect(lambda: self.showAbout())
        helpMenu.addAction(aboutAction)

        menuBar.addMenu(helpMenu)

        self.setMenuBar(menuBar)

    def showAbout(self):
        dialog = QDialog(parent=self)
        layout = QHBoxLayout()
        text = QLabel()
        text.setText("Digital pathology for local <i>in vivo</i> drug delivery.")
        layout.addWidget(text)
        dialog.setLayout(layout)
        dialog.setWindowTitle("About Broadside")

        dialog.exec_()


class Viewer:
    def __init__(self, *, app: QApplication):
        self.window = MainWindow()

        # self.sequence = SequenceModel(labels)
        # self.project = ProjectModel()

        # app.aboutToQuit()

    def show(self):
        self.window.show()
