from PySide2.QtWidgets import (
    QMainWindow,
    QAction,
    QMenuBar,
    QMenu,
    QLabel,
    QHBoxLayout,
    QDialog,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(parent=None)

        self.createMenuBar()

        self.setWindowTitle("Broadside")
        self.setMinimumHeight(500)
        self.setMinimumWidth(600)
        self.resize(1200, 800)  # w, h

    def createMenuBar(self) -> None:
        # set up actions
        self.openAction = QAction()
        self.openAction.setText("&Open")

        self.saveAction = QAction()
        self.saveAction.setText("&Save")
        self.saveAction.setShortcut("Ctrl+S")

        self.aboutAction = QAction()
        self.aboutAction.setText("About")
        self.aboutAction.triggered.connect(lambda: self.showAboutDialog())

        # set up menu bar
        menuBar: QMenuBar = self.menuBar()

        fileMenu: QMenu = menuBar.addMenu("&File")
        fileMenu.addAction(self.openAction)
        fileMenu.addAction(self.saveAction)

        helpMenu: QMenu = menuBar.addMenu("&Help")
        helpMenu.addAction(self.aboutAction)

    def showAboutDialog(self) -> None:
        text = QLabel()
        text.setText("Digital pathology for local <i>in vivo</i> drug delivery.")

        layout = QHBoxLayout()
        layout.addWidget(text)

        dialog = QDialog(parent=self)
        dialog.setLayout(layout)
        dialog.setWindowTitle("About Broadside")

        dialog.exec_()
