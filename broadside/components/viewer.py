import logging
from pathlib import Path
from typing import Type, Optional, List

from qtpy.QtGui import QCloseEvent
from qtpy.QtWidgets import QMessageBox

from .navigation import Navigator
from .steps import Step
from .steps.analysis import AnalysisStep
from .steps.annotation import AnnotationStep
from .steps.project import ProjectStep
from .utils import showSaveDialog, showSelectProjectDialog
from .viewer_model import ViewerModel
from .window import Window
from ..utils.events import EventEmitter


class Viewer:
    log = logging.getLogger(__name__)

    class Events:
        def __init__(self):
            self.theme = EventEmitter()

    def __init__(self, *, theme: str = "light", path: Path = None):
        self.events = self.Events()

        # editors
        self.current_step: Optional[Type[Step]] = None
        self.steps: List[Type[Step]] = [ProjectStep, AnnotationStep, AnalysisStep]

        # set up models
        step_names = [e.name for e in self.steps]
        self.navigator = Navigator(labels=step_names)
        self.model = ViewerModel()

        # set up user interface
        self._window = Window(navView=self.navigator._view)

        # set up bindings
        self.events.theme.connect(lambda theme: self._window.setTheme(theme))

        self._theme = None
        self.theme = theme

        self.init_bindings()

        if path is not None:
            self.model.path = path

    def show(self):
        # it's showtime
        self._window.show()

    @property
    def theme(self) -> str:
        return self._theme

    @theme.setter
    def theme(self, val: str) -> None:
        if self.theme != val:
            self._theme = val
            self.events.theme.emit(val)

    def toggle_theme(self) -> None:
        if self.theme == "light":
            self.theme = "dark"
        elif self.theme == "dark":
            self.theme = "light"

    def init_bindings(self):
        # from models
        self.navigator.model.events.index.connect(lambda _: self.update_editor())
        self.model.events.is_stale.connect(lambda _: self.update_window())
        self.model.events.path.connect(lambda _: self.update_window())

        # from view
        self._window.save_action.triggered.connect(lambda _: self.model.save())
        self._window.quit_action.triggered.connect(lambda _: self._window.close())
        self._window.open_action.triggered.connect(
            lambda _: self.on_path_change_requested()
        )
        self._window.aboutToClose.connect(lambda e: self.about_to_close(e))
        self._window.toggle_theme_action.triggered.connect(
            lambda _: self.toggle_theme()
        )

        # initialize
        self.update_window()
        self.update_editor()

    def update_window(self) -> None:
        # update title
        title = "Broadside"
        if self.model.is_set:
            name = self.model.path.name
            isStale = self.model.is_stale

            title += (f" – {name}" if name else "") + ("*" if isStale else "")

        self._window.setWindowTitle(title)

        # update menu
        self._window.save_action.setEnabled(self.model.is_set)

    def update_editor(self) -> None:
        self.log.debug("Update editor requested")

        if self.current_step is not None:
            # allow gc to work its magic
            self.current_step._view.setParent(None)

        index = self.navigator.model.index
        CurrentStep = self.steps[index]
        self.current_step = CurrentStep(model=self.model)
        self._window.setEditorView(self.current_step._view)

        # when editor is in a valid state, let navigator know
        def update_is_valid():
            self.navigator.model.is_valid = self.current_step.is_valid

        self.current_step.events.is_valid.connect(lambda _: update_is_valid())
        update_is_valid()

        # if project editor changes project, let viewer know
        if isinstance(self.current_step, ProjectStep):
            self.current_step: ProjectStep
            self.current_step.events.path_request.connect(
                lambda _: self.on_path_change_requested()
            )

        elif isinstance(self.current_step, AnnotationStep):
            self.current_step: AnnotationStep

            # self.current_editor.view.activeImageChanged.connect(
            #     lambda filename: self.update_window(filename=filename)
            # )

            # TODO: refactor this logic! figure out where else this is used
            # def onIsBusyChange():
            #     isBusy: bool = self.current_step._view.isBusy
            #     if isBusy:
            #         if QApplication.overrideCursor() != Qt.WaitCursor:
            #             QApplication.setOverrideCursor(Qt.WaitCursor)
            #         self._window.setEnabled(False)
            #     else:
            #         self._window.setEnabled(True)
            #         if QApplication.overrideCursor() == Qt.WaitCursor:
            #             QApplication.restoreOverrideCursor()
            #
            #     self.log.debug(f"isBusy changed to {isBusy}")
            #
            # self.current_step._view.isBusyChanged.connect(onIsBusyChange)
            # onIsBusyChange()

    def about_to_close(self, event: QCloseEvent) -> None:
        self.log.debug("About to close requested")

        if not self.model.is_set:
            self.model.on_close()
            self.log.debug("No project set; closing")
            event.accept()
            return

        name = self.model.path.name

        if not self.model.is_stale:
            self.model.on_close()
            self.log.debug(f"Project {name} has no changes; closing")
            event.accept()
            return

        response = showSaveDialog(
            parent=self._window,
            title="About to close",
            text=f"You have unsaved changes pending for project {name}.\n"
            "Do you want to save your changes?",
        )

        if response == QMessageBox.Save:
            self.model.save()
            self.model.on_close()
            self.log.debug(f"Project {name} saved; closing")
            event.accept()

        elif response == QMessageBox.Discard:
            self.model.on_close()
            self.log.debug(f"Project {name} not saved; closing")
            event.accept()

        elif response == QMessageBox.Cancel:
            self.log.debug(f"Project {name} not saved; not closing")
            event.ignore()

        else:
            raise RuntimeError(f"Unknown response {response}")

    def on_path_change_requested(self) -> None:
        self.log.debug("On project select requested")

        if self.model.is_stale:
            # ask user what to do since a save is pending
            name = self.model.path.name
            response = showSaveDialog(
                parent=self._window,
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

            self.model.is_stale = False

        new_path = showSelectProjectDialog(parent=self._window)
        if new_path is not None:
            self.model.path = new_path
            assert self.steps.index(ProjectStep) == 0
            self.navigator.model.index = 0
