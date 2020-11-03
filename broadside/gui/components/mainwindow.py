from PySide2.QtWidgets import QMainWindow, QAction, QMenuBar, QMenu


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(parent=None)
        self.createMenuBar()

        self.setWindowTitle("Broadside")
        self.setMinimumHeight(500)
        self.setMinimumWidth(600)
        self.resize(1200, 800)  # w, h

    def createMenuBar(self):
        # set up actions
        self.openAction = QAction()
        self.openAction.setText("&Open")

        self.saveAction = QAction()
        self.saveAction.setText("&Save")
        self.saveAction.setShortcut("Ctrl+S")

        self.aboutAction = QAction()
        self.aboutAction.setText("About")

        # set up menu bar
        menuBar: QMenuBar = self.menuBar()

        fileMenu: QMenu = menuBar.addMenu("&File")
        fileMenu.addAction(self.openAction)
        fileMenu.addAction(self.saveAction)

        helpMenu: QMenu = menuBar.addMenu("&Help")
        helpMenu.addAction(self.aboutAction)