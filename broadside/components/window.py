import logging
import warnings
from pathlib import Path

from napari._qt.qt_resources import get_stylesheet
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
global_stylesheet = (STYLES_DIR / "global.qss").read_text()
light_stylesheet = (STYLES_DIR / "light.qss").read_text()
dark_stylesheet = (STYLES_DIR / "dark.qss").read_text()

light_stylesheet_napari = get_stylesheet("light")
dark_stylesheet_napari = get_stylesheet("dark")


def show_about_dialog(parent: QWidget = None) -> None:
    label = QLabel()
    label.setText("Digital pathology for local <i>in vivo</i> drug delivery.")

    layout = QHBoxLayout()
    layout.addWidget(label)

    dialog = QDialog(parent=parent)
    dialog.setWindowModality(Qt.ApplicationModal)
    dialog.setLayout(layout)
    dialog.setWindowTitle("About")

    dialog.exec_()


class Window(QMainWindow):
    log = logging.getLogger(__name__)

    about_to_close = Signal(QCloseEvent)

    def __init__(self, *, nav_view: QWidget):
        super().__init__(parent=None)

        self.setFocusPolicy(Qt.StrongFocus)
        self.setWindowTitle("Broadside")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        self.resize(1200, 800)  # w, h

        self.init_menu_bar()
        self.init_bindings()
        self.init_layout(navView=nav_view)

    def init_menu_bar(self) -> None:
        # set up actions
        open_action = QAction()
        open_action.setText("&Open")
        self.open_action = open_action

        save_action = QAction()
        save_action.setText("&Save")
        save_action.setShortcut("Ctrl+S")
        self.save_action = save_action

        about_action = QAction()
        about_action.setText("About")
        self.about_action = about_action

        quit_action = QAction()
        quit_action.setText("&Quit")
        quit_action.setShortcut("Ctrl+Q")
        self.quit_action = quit_action

        toggle_theme_action = QAction()
        toggle_theme_action.setText("Toggle theme")
        toggle_theme_action.setShortcut("Ctrl+Shift+T")
        self.toggle_theme_action = toggle_theme_action

        # set up menu bar
        menuBar: QMenuBar = self.menuBar()

        file_menu: QMenu = menuBar.addMenu("&File")
        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addSeparator()
        file_menu.addAction(quit_action)

        view_menu: QMenu = menuBar.addMenu("&View")
        view_menu.addAction(toggle_theme_action)

        help_menu: QMenu = menuBar.addMenu("&Help")
        help_menu.addAction(about_action)

    def init_bindings(self) -> None:
        self.about_action.triggered.connect(lambda: show_about_dialog(self))

    def init_layout(self, *, navView: QWidget) -> None:
        editor_layout = QVBoxLayout()
        editor_layout.setSpacing(0)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.addWidget(QWidget(), stretch=0)
        editor_layout.addWidget(QWidget(), stretch=1)
        self.editor_layout = editor_layout

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(QHLine())
        layout.addWidget(navView, stretch=0)
        layout.addWidget(QHLine())
        layout.addLayout(self.editor_layout, stretch=1)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def set_theme(self, theme: str) -> None:
        """
        Since reading text files is slow, maybe cache them?
        """
        if theme not in ["dark", "light"]:
            warnings.warn(f"Theme {theme} not supported! Defaulting to light")
            theme = "light"

        stylesheet = light_stylesheet if theme == "light" else dark_stylesheet
        self.setStyleSheet(global_stylesheet + "\n" + stylesheet)

        self.log.debug(f"Theme set to {theme}")

    def closeEvent(self, event: QCloseEvent) -> None:
        """
        To be able to handle both the user calling quit and clicking the close button,
        we hijack the window close event and handle it in the window's controller
        (`Viewer`).
        """

        self.about_to_close.emit(event)

    def set_editor_view(self, widget: QWidget) -> None:
        """
        Whenever this runs, there is a brief flash of improperly aligned content where
        the navigator widget appears in the middle of the layout. To prevent this, we
        add a dummy QWidget initially with zero stretch (when the project step is
        loaded), and whenever the navigator steps forwards or backwards, the step widget
        is taken, the dummy widget stretch is set to 1, the new step widget is loaded,
        and the dummy widget stretch is set back to 0. It's hacky, but it works.
        """

        # delete old widget ...
        item: QLayoutItem = self.editor_layout.takeAt(1)

        self.editor_layout.setStretch(0, 1)

        if (item is not None) and (item.widget() is not None):
            oldWidget: QWidget = item.widget()
            oldWidget.deleteLater()

        # ... and set new widget
        self.editor_layout.addWidget(widget)

        self.editor_layout.setStretch(0, 0)
