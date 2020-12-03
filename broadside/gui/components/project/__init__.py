import logging
from pathlib import Path

from PySide2.QtCore import Signal

from .device import DeviceListEditor
from .image import ImageListEditor
from .samplegroup import SampleGroupListEditor
from .view import ProjectView
from ..editor import BaseEditor


class ProjectEditor(BaseEditor):
    log = logging.getLogger(__name__)

    name = "Project"

    # signals to parent
    projectSelectRequested = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.view = ProjectView()

        # reactivity
        self.view.selectProjectButton.clicked.connect(
            lambda: self.projectSelectRequested.emit()
        )
        self.model.pathChanged.connect(lambda: self.refreshView())
        self.refreshView()

        # logging
        self.projectSelectRequested.connect(
            lambda: self.log.info("projectSelectRequested emitted")
        )

    def beforeDelete(self) -> None:
        self.model.pathChanged.disconnect(self.refreshView)

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
        sampleGroupListEditor = SampleGroupListEditor()
        imageListEditor = ImageListEditor()

        deviceListEditor.dataChanged.connect(lambda: self.dataChanged.emit())

        self.view.onProjectSelected(
            description=self.model.description,
            deviceListView=deviceListEditor.view,
            sampleGroupListView=sampleGroupListEditor.view,
            imageListView=imageListEditor.view,
        )

        # any subsequent changes in view are propagated to model
        def setDescriptionText():
            description = self.view.descriptionTextEdit.toPlainText()
            self.model.description = description

        self.view.descriptionTextEdit.textChanged.connect(lambda: setDescriptionText())

        # the editor is complete when a project is set (for now at least)
        self.isComplete = True
