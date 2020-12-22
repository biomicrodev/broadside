import logging
from pathlib import Path

from PySide2.QtCore import Signal

from .block import BlockListEditor
from .device import DeviceListEditor
from .image import ImageListEditor
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
        self.blockListEditor = None
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

        blockListEditor = BlockListEditor(self.model)
        blockListEditor.dataChanged.connect(lambda: self.dataChanged.emit())

        # how to best hook up functionality in one widget that is dependent on a
        # far-away widget...
        def updateDeviceNames():
            names = [d.name for d in self.model.devices]
            blockListEditor.view.updateDeviceNames(names)

        self.dataChanged.connect(lambda: updateDeviceNames())
        updateDeviceNames()
        self.blockListEditor = blockListEditor

        imageListEditor = ImageListEditor()
        # imageListEditor.dataChanged.connect(lambda: self.dataChanged.emit())

        self.view.onProjectSelected(
            description=self.model.description,
            deviceListView=deviceListEditor.view,
            blockListView=blockListEditor.view,
            imageListView=imageListEditor.view,
        )

        # any subsequent changes in this widget are propagated to model; the rest of
        # the views handle their own changes
        def setDescriptionText():
            description = self.view.descriptionTextEdit.toPlainText()
            self.model.description = description

        self.view.descriptionTextEdit.textChanged.connect(lambda: setDescriptionText())

    def validate(self):
        isDeviceListEditorValid = (
            self.deviceListEditor.isValid
            if self.deviceListEditor is not None
            else False
        )

        isBlockListEditorValid = (
            self.blockListEditor.isValid if self.blockListEditor is not None else False
        )

        self.isValid = (
            isDeviceListEditorValid
            & isBlockListEditorValid
            & (self.model.path is not None)
        )

        self.log.info(f"validated to {str(self.isValid)}")
