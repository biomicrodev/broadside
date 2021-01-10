import logging
from pathlib import Path

from PySide2.QtCore import Qt, Signal, QEvent
from PySide2.QtGui import QCloseEvent
from PySide2.QtWidgets import (
    QMainWindow,
    QAction,
    QMenuBar,
    QMenu,
    QWidget,
    QDialog,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
)

from .utils import QHLine

STYLES_DIR = Path(__file__).parents[1].resolve() / "resources" / "styles"


def showAboutDialog(parent: QWidget = None) -> None:
    label = QLabel()
    label.setText("Digital pathology for local <i>in vivo</i> drug delivery.")

    layout = QHBoxLayout()
    layout.addWidget(label)

    dialog = QDialog(parent=parent)
    dialog.setWindowModality(Qt.ApplicationModal)
    dialog.setLayout(layout)
    dialog.setWindowTitle("About")

    dialog.exec_()


class MainWindow(QMainWindow):
    log = logging.getLogger(__name__)

    aboutToClose = Signal(QCloseEvent)

    def __init__(self, navWidget: QWidget, *, theme: str = "light"):
        super().__init__(parent=None)

        self.navWidget = navWidget
        self.theme = theme

        self.hide()
        self.setFocusPolicy(Qt.StrongFocus)
        self.setWindowTitle("Broadside")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        self.resize(1200, 800)  # w, h

        self.initMenuBar()
        self.initBindings()
        self.initLayout()

        self.applyStyleSheet()

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
        self.aboutAction = aboutAction

        quitAction = QAction()
        quitAction.setText("&Quit")
        quitAction.setShortcut("Ctrl+Q")
        self.quitAction = quitAction

        toggleThemeAction = QAction()
        toggleThemeAction.setText("Toggle theme")
        toggleThemeAction.setShortcut("Ctrl+Shift+T")
        self.toggleThemeAction = toggleThemeAction

        # set up menu bar
        menuBar: QMenuBar = self.menuBar()

        fileMenu: QMenu = menuBar.addMenu("&File")
        fileMenu.addAction(openAction)
        fileMenu.addAction(saveAction)
        fileMenu.addSeparator()
        fileMenu.addAction(quitAction)

        viewMenu: QMenu = menuBar.addMenu("&View")
        viewMenu.addAction(toggleThemeAction)

        helpMenu: QMenu = menuBar.addMenu("&Help")
        helpMenu.addAction(aboutAction)

    def initBindings(self) -> None:
        self.aboutAction.triggered.connect(lambda: showAboutDialog(self))

    def initLayout(self) -> None:
        editorViewContainer = QVBoxLayout()
        editorViewContainer.setSpacing(0)
        editorViewContainer.setContentsMargins(0, 0, 0, 0)
        editorViewContainer.addWidget(QWidget())
        self.editorViewContainer = editorViewContainer

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.navWidget, stretch=0)
        layout.addWidget(QHLine(), stretch=0)
        layout.addLayout(self.editorViewContainer, stretch=1)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def toggleTheme(self) -> None:
        if self.theme == "light":
            self.theme = "dark"
        elif self.theme == "dark":
            self.theme = "light"

        self.applyStyleSheet()

    def applyStyleSheet(self) -> None:
        filepath = STYLES_DIR / f"{self.theme}.qss"
        stylesheet = filepath.read_text()
        self.setStyleSheet(stylesheet)

        self.log.info(f"Theme set to {self.theme}")

    def closeEvent(self, event: QCloseEvent) -> None:
        """
        To be able to handle both the user calling quit and clicking the close button,
        we hijack the window close event and handle it in the window's controller
        (`Viewer`).
        """

        self.aboutToClose.emit(event)

    def setEditorView(self, widget: QWidget) -> None:
        # delete old widget ...
        oldWidget: QWidget = self.editorViewContainer.itemAt(0).widget()
        oldWidget.deleteLater()

        # ... and set new widget
        self.editorViewContainer.addWidget(widget)
