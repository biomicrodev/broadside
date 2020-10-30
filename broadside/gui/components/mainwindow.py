from PySide2.QtWidgets import QMainWindow, QMenu, QAction, QMenuBar


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(parent=None)
        self.setWindowTitle("Broadside")
        self.createMenuBar()

        self.setMinimumHeight(500)
        self.setMinimumWidth(600)
        self.resize(1200, 800)  # w, h

    def createMenuBar(self):
        # set up actions
        self.openAction = QAction()
        self.openAction.setText("&Open")

        self.saveAction = QAction()
        self.saveAction.setText("&Save")

        self.aboutAction = QAction()
        self.aboutAction.setText("About")

        # set up menu bar
        menuBar: QMenuBar = self.menuBar()

        fileMenu = menuBar.addMenu("&File")
        fileMenu.setTitle("&File")
        fileMenu.addAction(self.openAction)
        fileMenu.addAction(self.saveAction)

        helpMenu = menuBar.addMenu("&Help")
        helpMenu.setTitle("&Help")
        helpMenu.addAction(self.aboutAction)
