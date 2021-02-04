import logging
from pathlib import Path

from qtpy.QtCore import Qt, Signal
from qtpy.QtGui import QCloseEvent
from qtpy.QtWidgets import (
    QMainWindow,
    QAction,
    QMenuBar,
    QMenu,
    QWidget,
    QDialog,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QLayoutItem,
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
        editorLayout = QVBoxLayout()
        editorLayout.setSpacing(0)
        editorLayout.setContentsMargins(0, 0, 0, 0)
        editorLayout.addWidget(QWidget())
        self.editorLayout = editorLayout

        parentLayout = QVBoxLayout()
        parentLayout.setContentsMargins(0, 0, 0, 0)
        parentLayout.setSpacing(0)
        parentLayout.addWidget(self.navWidget, stretch=0)
        parentLayout.addWidget(QHLine(), stretch=0)
        parentLayout.addLayout(self.editorLayout, stretch=1)

        parentWidget = QWidget()
        parentWidget.setLayout(parentLayout)
        self.setCentralWidget(parentWidget)

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
        item: QLayoutItem = self.editorLayout.takeAt(0)
        if item.widget() is not None:
            item.widget().deleteLater()

        # ... and set new widget
        self.editorLayout.addWidget(widget)
