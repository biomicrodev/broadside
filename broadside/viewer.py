import logging
from pathlib import Path
from typing import Optional, Type, List

from PySide2.QtGui import QCloseEvent
from PySide2.QtWidgets import QApplication, QMessageBox, QWidget

from .components.analysis import AnalysisEditor
from .components.annotation import AnnotationEditor
from .components.editor import Editor
from .components.mainwindow import MainWindow
from .components.navigation import Navigator
from .components.project import ProjectEditor
from .components.utils import showSaveDialog, showSelectProjectDialog
from .components.session import Session


class Viewer:
    log = logging.getLogger(__name__)

    def __init__(self, app: QApplication, *, theme: str = "light", path: Path = None):
        self.app = app  # or should I use QApplication.instance()?
        self.theme = theme

        self.current_editor: Optional[Type[Editor]] = None
        self.editors: List[Type[Editor]] = [
            ProjectEditor,
            AnnotationEditor,
            AnalysisEditor,
        ]

        editor_names = [e.name for e in self.editors]

        # set up models and views
        self.navigator = Navigator(editor_names)
        self.view = MainWindow()
        self.view.initCentralWidget(self.navigator.view)
        self.project_model = Session()

        self.init_reactivity()

        # it's showtime
        self.view.show()

        if path is not None:
            self.project_model.path = path

    def init_reactivity(self):
        # from model
        self.navigator.model.indexChanged.connect(lambda: self.update_editor())
        self.project_model.isStaleChanged.connect(lambda: self.update_window())
        self.project_model.pathChanged.connect(lambda: self.update_window())

        # from view
        self.view.saveAction.triggered.connect(lambda: self.project_model.save())
        self.view.quitAction.triggered.connect(lambda: self.view.close())
        self.view.openAction.triggered.connect(lambda: self.on_path_change_requested())
        self.view.aboutToClose.connect(lambda e: self.about_to_quit(e))
        self.view.toggleThemeAction.triggered.connect(lambda: self.toggle_theme())

        # initialize
        self.view.applyStyleSheet(self.theme)
        self.update_window()
        self.update_editor()

    def toggle_theme(self) -> None:
        if self.theme == "light":
            self.theme = "dark"
        elif self.theme == "dark":
            self.theme = "light"

        self.view.applyStyleSheet(self.theme)

        self.log.info(f"Theme toggled to {self.theme}")

    def update_window(self) -> None:
        self.log.info("Update window requested")

        # update title
        name = self.project_model.name
        isStale = self.project_model.isStale

        title = "Broadside" + (f" – {name}" if name else "") + ("*" if isStale else "")
        self.view.setWindowTitle(title)

        # update menu
        path = self.project_model.path
        self.view.saveAction.setEnabled(path is not None)

    def update_editor(self) -> None:
        self.log.info("Update editor requested")

        # delete current widget...
        if self.current_editor is not None:
            # self.current_editor.beforeDelete()
            del self.current_editor

        widget: QWidget = self.view.editorViewContainer.itemAt(0).widget()
        widget.deleteLater()

        # ... and add the next one
        index = self.navigator.model.index
        Editor = self.editors[index]
        self.current_editor = Editor(model=self.project_model)
        self.view.editorViewContainer.addWidget(self.current_editor.view)

        # when editor is complete, let viewer know
        def update_is_valid():
            self.navigator.model.isValid = self.current_editor.isValid

        self.current_editor.isValidChanged.connect(lambda: update_is_valid())
        update_is_valid()

        # if project editor changes project, let viewer know
        if isinstance(self.current_editor, ProjectEditor):
            self.current_editor.pathChangeRequested.connect(
                lambda: self.on_path_change_requested()
            )

        # if data has changed in editor, let viewer know
        def setStale():
            self.project_model.isStale = True

        self.current_editor.dataChanged.connect(lambda: setStale())

    def about_to_quit(self, event: QCloseEvent) -> None:
        self.log.info("About to quit requested")

        if self.project_model.path is None:
            self.log.info("No project set; quitting")
            event.accept()
            return

        name = self.project_model.name

        if not self.project_model.isStale:
            self.log.info(f"Project {name} has no changes; quitting")
            event.accept()
            return

        response = showSaveDialog(
            parent=self.view,
            title="About to quit",
            text=f"You have unsaved changes pending for project {name}.\n"
            "Do you want to save your changes?",
        )
        if response == QMessageBox.Save:
            self.project_model.save()
            self.log.info(f"Project {name} saved; quitting")
            event.accept()
        elif response == QMessageBox.Discard:
            self.log.info(f"Project {name} not saved; quitting")
            event.accept()
        elif response == QMessageBox.Cancel:
            self.log.info(f"Project {name} not saved; not quitting")
            event.ignore()

    def on_path_change_requested(self) -> None:
        self.log.info("On project select requested")

        if self.project_model.isStale:
            # ask user what to do since a save is pending
            name = self.project_model.name
            response = showSaveDialog(
                parent=self.view,
                title="Unsaved changes",
                text=f"You have unsaved changes pending for project {name}.\n"
                "Do you want to save your changes?",
            )

            if response == QMessageBox.Save:
                self.project_model.save()
            elif response == QMessageBox.Discard:
                pass
            elif response == QMessageBox.Cancel:
                return
            else:
                raise RuntimeError(f"Unknown response {response}")

            self.project_model.isStale = False

        new_path = showSelectProjectDialog(parent=self.view)
        if new_path is not None:
            self.project_model.path = new_path
            self.navigator.model.index = self.editors.index(ProjectEditor)
