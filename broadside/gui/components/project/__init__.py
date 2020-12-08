import logging
from pathlib import Path

from PySide2.QtCore import Signal

from .device import DeviceListEditor
from .image import ImageListEditor
from .samplegroup import SampleGroupListEditor
from .view import ProjectView
from ..editor import Editor
from ...models.project import ProjectModel


class ProjectEditor(Editor):
    log = logging.getLogger(__name__)

    name = "Project"

    # signals to parent
    projectSelectRequested = Signal()

    def __init__(self, model: ProjectModel, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.model = model
        self.view = ProjectView()

        # editors
        self.deviceListEditor = None
        self.sampleGroupListEditor = None
        self.imageListEditor = None

        # reactivity
        self.view.selectProjectButton.clicked.connect(
            lambda: self.projectSelectRequested.emit()
        )
        self.model.pathChanged.connect(lambda: self.refreshView())
        self.model.pathChanged.connect(lambda: self.validate())
        self.dataChanged.connect(lambda: self.validate())

        self.refreshView()
        self.validate()

        # logging
        self.projectSelectRequested.connect(
            lambda: self.log.info("projectSelectRequested emitted")
        )

    def refreshView(self) -> None:
        # update project labels
        path: Path = self.model.path
        path: str = str(path.parent) if path else "none"

        name: str = self.model.name
        name: str = name if name else "none"

        self.view.setProjectLabels(path=path, name=name)

        if not self.model.path:
            return

        # update project editors
        # populate view using model
        deviceListEditor = DeviceListEditor(self.model.devices)
        deviceListEditor.dataChanged.connect(lambda: self.dataChanged.emit())
        self.deviceListEditor = deviceListEditor

        sampleGroupListEditor = SampleGroupListEditor(self.model.sampleGroups)
        sampleGroupListEditor.dataChanged.connect(lambda: self.dataChanged.emit())
        self.sampleGroupListEditor = sampleGroupListEditor

        imageListEditor = ImageListEditor()
        # imageListEditor.dataChanged.connect(lambda: self.dataChanged.emit())

        self.view.onProjectSelected(
            description=self.model.description,
            deviceListView=deviceListEditor.view,
            sampleGroupListView=sampleGroupListEditor.view,
            imageListView=imageListEditor.view,
        )

        # any subsequent changes in this widget are propagated to model; the rest of
        # the views handle their own changes
        def setDescriptionText():
            description = self.view.descriptionTextEdit.toPlainText()
            self.model.description = description

        self.view.descriptionTextEdit.textChanged.connect(lambda: setDescriptionText())

    def validate(self):
        self.isValid = (
            (
                self.deviceListEditor.isValid
                if self.deviceListEditor is not None
                else False
            )
            & (
                self.sampleGroupListEditor.isValid
                if self.sampleGroupListEditor is not None
                else False
            )
            & (self.model.path is not None)
        )

        self.log.info(f"validated to {str(self.isValid)}")
