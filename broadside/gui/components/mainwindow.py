from pathlib import Path
from typing import List

from PySide2.QtCore import Qt, Signal
from PySide2.QtGui import QCloseEvent
from PySide2.QtWidgets import (
    QMainWindow,
    QAction,
    QMenuBar,
    QMenu,
    QLabel,
    QHBoxLayout,
    QDialog,
    QVBoxLayout,
    QWidget,
    QFrame,
)

from .navigation.view import NavigationWidget
from ..utils import QHLine

STYLES_DIR = Path(__file__).parents[2].resolve() / "resources" / "styles"


class MainWindow(QMainWindow):
    aboutToClose = Signal(QCloseEvent)

    def __init__(self):
        super().__init__(parent=None)

        self.initMenuBar()

        self.setWindowTitle("Broadside")
        self.setMinimumHeight(500)
        self.setMinimumWidth(600)
        self.resize(1200, 800)  # w, h

        self.initStyleSheet()

    def initMenuBar(self) -> None:
        # set up actions
        openAction = QAction()
        openAction.setText("&Open")
        self.openAction = openAction

        saveAction = QAction()
        saveAction.setText("&Save")
        saveAction.setShortcut("Ctrl+S")
        self.saveAction = saveAction

        aboutAction = QAction()
        aboutAction.setText("About")
        aboutAction.triggered.connect(lambda: self.showAboutDialog())
        self.aboutAction = aboutAction

        quitAction = QAction()
        quitAction.setText("&Quit")
        quitAction.setShortcut("Ctrl+Q")
        self.quitAction = quitAction

        # set up menu bar
        menuBar: QMenuBar = self.menuBar()

        fileMenu: QMenu = menuBar.addMenu("&File")
        fileMenu.addAction(self.openAction)
        fileMenu.addAction(self.saveAction)
        fileMenu.addSeparator()
        fileMenu.addAction(self.quitAction)

        helpMenu: QMenu = menuBar.addMenu("&Help")
        helpMenu.addAction(self.aboutAction)

    def showAboutDialog(self) -> None:
        text = QLabel()
        text.setText("Digital pathology for local <i>in vivo</i> drug delivery.")

        layout = QHBoxLayout()
        layout.addWidget(text)

        dialog = QDialog(parent=self)
        dialog.setWindowModality(Qt.ApplicationModal)
        dialog.setLayout(layout)
        dialog.setWindowTitle("About")

        dialog.exec_()

    def initCentralWidget(self, panelNames: List[str]) -> None:
        self.navPanel = NavigationWidget(labels=panelNames)

        panelContainer = QVBoxLayout()
        panelContainer.setSpacing(0)
        panelContainer.setContentsMargins(0, 0, 0, 0)
        panelContainer.addWidget(QWidget())
        self.panelContainer = panelContainer

        centralLayout = QVBoxLayout()
        centralLayout.setContentsMargins(0, 0, 0, 0)
        centralLayout.setSpacing(0)
        centralLayout.addWidget(self.navPanel, stretch=0)
        centralLayout.addWidget(QHLine(), stretch=0)
        centralLayout.addLayout(self.panelContainer, stretch=1)

        widget = QWidget()
        widget.setLayout(centralLayout)
        self.setCentralWidget(widget)

    def initStyleSheet(self, style: str = "default") -> None:
        filepath = STYLES_DIR / f"{style}.qss"

        if not filepath.is_file():
            filepath = STYLES_DIR / "default.qss"

        with open(str(filepath), "r") as file:
            self.setStyleSheet(file.read())

    def closeEvent(self, event: QCloseEvent):
        self.aboutToClose.emit(event)
