import logging
from pathlib import Path
from typing import Optional, Type, List

from qtpy.QtCore import Qt
from qtpy.QtGui import QCloseEvent
from qtpy.QtWidgets import QApplication, QMessageBox

from .components.analysis import AnalysisEditor
from .components.annotation import AnnotationEditor
from .components.editor import Editor
from .components.mainwindow import MainWindow
from .components.navigation import Navigator
from .components.project import ProjectEditor
from .components.utils import showSaveDialog, showSelectProjectDialog
from .components.viewermodel import ViewerModel


class Viewer:
    log = logging.getLogger(__name__)

    def __init__(self, *, theme: str = "light", path: Path = None):
        self.current_editor: Optional[Type[Editor]] = None
        self.editors: List[Type[Editor]] = [
            ProjectEditor,
            AnnotationEditor,
            AnalysisEditor,
        ]

        # set up models and views
        editor_names = [e.name for e in self.editors]
        self.navigator = Navigator(editor_names)
        self.model = ViewerModel()

        self.view = MainWindow(self.navigator.view, theme=theme)
        self.view.initLayout()

        self.init_bindings()

        # it's showtime
        self.view.show()

        if path is not None:
            self.model.path = path

    def init_bindings(self):
        # from model
        self.navigator.model.indexChanged.connect(lambda: self.update_editor())
        self.model.isStaleChanged.connect(lambda: self.update_window())
        self.model.pathChanged.connect(lambda: self.update_window())

        # from view
        self.view.saveAction.triggered.connect(lambda: self.model.save())
        self.view.quitAction.triggered.connect(lambda: self.view.close())
        self.view.openAction.triggered.connect(lambda: self.on_path_change_requested())
        self.view.aboutToClose.connect(lambda e: self.about_to_close(e))
        self.view.toggleThemeAction.triggered.connect(lambda: self.view.toggleTheme())

        # initialize
        self.update_window()
        self.update_editor()

    def update_window(self, filename: str = "") -> None:
        if self.model.isSet:
            # update title
            name = self.model.name
            isStale = self.model.isStale

            title = (
                "Broadside"
                + (f" – {name}" if name else "")
                + ("*" if isStale else "")
                + (f" – {filename}" if filename else "")
            )
        else:
            title = "Broadside"

        self.view.setWindowTitle(title)

        # update menu
        self.view.saveAction.setEnabled(self.model.isSet)

    def update_editor(self) -> None:
        self.log.info("Update editor requested")

        index = self.navigator.model.index
        Editor = self.editors[index]
        self.current_editor = Editor(model=self.model)
        self.view.setEditorView(self.current_editor.view)

        # when editor is in a valid state, let navigator know
        def update_is_valid():
            self.navigator.model.isValid = self.current_editor.isValid

        self.current_editor.isValidChanged.connect(lambda: update_is_valid())
        update_is_valid()

        # if project editor changes project, let viewer know
        if isinstance(self.current_editor, ProjectEditor):
            self.current_editor: ProjectEditor
            self.current_editor.pathChangeRequested.connect(
                lambda: self.on_path_change_requested()
            )

        elif isinstance(self.current_editor, AnnotationEditor):
            self.current_editor: AnnotationEditor

            # self.current_editor.view.activeImageChanged.connect(
            #     lambda filename: self.update_window(filename=filename)
            # )

            # TODO: refactor this logic! figure out where else this is used
            def onIsBusyChange():
                isBusy: bool = self.current_editor.view.isBusy
                if isBusy:
                    if QApplication.overrideCursor() != Qt.WaitCursor:
                        QApplication.setOverrideCursor(Qt.WaitCursor)
                    self.view.setEnabled(False)
                else:
                    self.view.setEnabled(True)
                    if QApplication.overrideCursor() == Qt.WaitCursor:
                        QApplication.restoreOverrideCursor()

                self.log.info(f"isBusy changed to {isBusy}")

            self.current_editor.view.isBusyChanged.connect(onIsBusyChange)
            onIsBusyChange()

        # if data has changed in editor, let viewer know
        def set_stale():
            self.model.isStale = True

        self.current_editor.dataChanged.connect(lambda: set_stale())

    def about_to_close(self, event: QCloseEvent) -> None:
        self.log.info("About to close requested")

        if not self.model.isSet:
            self.model.close()
            self.log.info("No project set; closing")
            event.accept()
            return

        name = self.model.name

        if not self.model.isStale:
            self.model.close()
            self.log.info(f"Project {name} has no changes; closing")
            event.accept()
            return

        response = showSaveDialog(
            parent=self.view,
            title="About to close",
            text=f"You have unsaved changes pending for project {name}.\n"
            "Do you want to save your changes?",
        )
        if response == QMessageBox.Save:
            self.model.save()
            self.model.close()
            self.log.info(f"Project {name} saved; closing")
            event.accept()
        elif response == QMessageBox.Discard:
            self.model.close()
            self.log.info(f"Project {name} not saved; closing")
            event.accept()
        elif response == QMessageBox.Cancel:
            self.log.info(f"Project {name} not saved; not closing")
            event.ignore()
        else:
            raise RuntimeError(f"Unknown response {response}")

    def on_path_change_requested(self) -> None:
        self.log.info("On project select requested")

        if self.model.isStale:
            # ask user what to do since a save is pending
            name = self.model.name
            response = showSaveDialog(
                parent=self.view,
                title="Unsaved changes",
                text=f"You have unsaved changes pending for project {name}.\n"
                "Do you want to save your changes?",
            )

            if response == QMessageBox.Save:
                self.model.save()
            elif response == QMessageBox.Discard:
                pass
            elif response == QMessageBox.Cancel:
                return
            else:
                raise RuntimeError(f"Unknown response {response}")

            self.model.isStale = False

        new_path = showSelectProjectDialog(parent=self.view)
        if new_path is not None:
            self.model.path = new_path
            assert self.editors.index(ProjectEditor) == 0
            self.navigator.model.index = 0
