import logging
from pathlib import Path
from typing import Optional, Type, List

from PySide2.QtCore import QObject, Signal, Qt, QDir
from PySide2.QtGui import QCloseEvent
from PySide2.QtWidgets import QApplication, QMessageBox, QFileDialog, QWidget

from .components.analysis import AnalysisEditor
from .components.annotation import AnnotationEditor
from .components.editor import Editor
from .components.mainwindow import MainWindow
from .components.navigation import Navigator
from .components.project import ProjectEditor
from .components.utils import showSaveDialog
from .models.project import ProjectModel


def showSelectProjectDialog(parent: QWidget = None) -> Optional[Path]:
    dialog = QFileDialog(parent, Qt.Dialog)
    dialog.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog)
    dialog.setAcceptMode(QFileDialog.AcceptSave)
    dialog.setLabelText(QFileDialog.LookIn, "Select project folder")
    dialog.setFileMode(QFileDialog.Directory)
    dialog.setOption(QFileDialog.ShowDirsOnly, True)
    dialog.setViewMode(QFileDialog.Detail)
    dialog.setDirectory(QDir.homePath())

    if dialog.exec_():
        paths = dialog.selectedFiles()
        assert len(paths) == 1
        path = Path(paths[0])
        return path

    return None


class Viewer:
    log = logging.getLogger(__name__)

    def __init__(self, app: QApplication, *, theme: str = "light", path: Path = None):
        self.app = app
        self.app.setStyle("Fusion")

        self.theme = theme

        self.currentEditor: Optional[Type[Editor]] = None
        self.editors: List[Type[Editor]] = [
            ProjectEditor,
            AnnotationEditor,
            AnalysisEditor,
        ]

        editorNames: List[str] = [e.name for e in self.editors]

        # set up models and views
        self.navigator = Navigator(editorNames)
        self.view = MainWindow()
        self.view.initCentralWidget(self.navigator.view)
        self.projectModel = ProjectModel()

        self.initReactivity()

        # it's showtime
        self.view.show()

        if path is not None:
            self.projectModel.path = path

    def initReactivity(self):
        # from model
        self.navigator.model.indexChanged.connect(lambda: self.updateEditor())
        self.projectModel.isStaleChanged.connect(lambda: self.updateWindow())
        self.projectModel.pathChanged.connect(lambda: self.updateWindow())

        # from view
        self.view.saveAction.triggered.connect(lambda: self.projectModel.save())
        self.view.quitAction.triggered.connect(lambda: self.view.close())
        self.view.openAction.triggered.connect(lambda: self.onProjectSelectRequest())
        self.view.aboutToClose.connect(lambda e: self.aboutToQuit(e))
        self.view.toggleThemeAction.triggered.connect(lambda: self.toggleTheme())

        # initialize
        self.view.applyStyleSheet(self.theme)
        self.updateWindow()
        self.updateEditor()

    def toggleTheme(self) -> None:
        if self.theme == "light":
            self.theme = "dark"
        elif self.theme == "dark":
            self.theme = "light"

        self.view.applyStyleSheet(self.theme)

        self.log.info(f"Theme toggled to {self.theme}")

    def updateWindow(self) -> None:
        self.log.info("Update window requested")

        # update title
        name = self.projectModel.name
        isStale = self.projectModel.isStale

        title = "Broadside" + (f" – {name}" if name else "") + ("*" if isStale else "")
        self.view.setWindowTitle(title)

        # update menu
        path = self.projectModel.path
        self.view.saveAction.setEnabled(path is not None)

    def updateEditor(self) -> None:
        self.log.info("Update editor requested")

        # delete current widget...
        if self.currentEditor is not None:
            self.currentEditor.beforeDelete()
            del self.currentEditor

        widget: QWidget = self.view.editorViewContainer.itemAt(0).widget()
        widget.deleteLater()

        # ... and add the next one
        index = self.navigator.model.index
        Editor = self.editors[index]
        self.currentEditor = Editor(model=self.projectModel)
        self.view.editorViewContainer.addWidget(self.currentEditor.view)

        # when editor is complete, let viewer know
        def updateIsValid():
            self.navigator.model.isValid = self.currentEditor.isValid

        self.currentEditor.isValidChanged.connect(updateIsValid)
        updateIsValid()

        # if project editor changes project, let viewer know
        if isinstance(self.currentEditor, ProjectEditor):
            self.currentEditor.projectSelectRequested.connect(
                lambda: self.onProjectSelectRequest()
            )

        # if data has changed in editor, let viewer know
        def setStale():
            self.projectModel.isStale = True

        self.currentEditor.dataChanged.connect(lambda: setStale())

    def aboutToQuit(self, event: QCloseEvent) -> None:
        self.log.info("About to quit requested")

        if self.projectModel.path is None:
            self.log.info("No project set; quitting")
            event.accept()
            return

        name = self.projectModel.name

        if not self.projectModel.isStale:
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
            self.projectModel.save()
            self.log.info(f"Project {name} saved; quitting")
            event.accept()
        elif response == QMessageBox.Discard:
            self.log.info(f"Project {name} not saved; quitting")
            event.accept()
        elif response == QMessageBox.Cancel:
            self.log.info(f"Project {name} not saved; not quitting")
            event.ignore()

    def onProjectSelectRequest(self) -> None:
        self.log.info("On project select requested")

        if self.projectModel.isStale:
            # ask user what to do since a save is pending
            name = self.projectModel.name
            response = showSaveDialog(
                parent=self.view,
                title="Unsaved changes",
                text=f"You have unsaved changes pending for project {name}.\n"
                "Do you want to save your changes?",
            )

            if response == QMessageBox.Save:
                self.projectModel.save()
            elif response == QMessageBox.Discard:
                pass
            elif response == QMessageBox.Cancel:
                return
            else:
                raise RuntimeError(f"Unknown response {response}")

            self.projectModel.isStale = False

        newPath = showSelectProjectDialog(parent=self.view)
        if newPath is not None:
            self.projectModel.path = newPath
            self.navigator.model.index = self.editors.index(ProjectEditor)
