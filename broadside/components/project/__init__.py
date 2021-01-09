import logging
from pathlib import Path
from typing import Optional

from PySide2.QtCore import Signal
from PySide2.QtWidgets import QTabBar

from .block import BlockListEditor
from .device import DeviceListEditor
from .image import ImageListEditor
from .panel import PanelListEditor
from .view import ProjectView
from ..color import Color
from ..editor import Editor
from ..viewermodel import ViewerModel


class ProjectEditor(Editor):
    log = logging.getLogger(__name__)

    name = "Project"

    # signals to parent
    pathChangeRequested = Signal()

    def __init__(self, model: ViewerModel, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.model = model
        self.view = ProjectView()

        # editors
        self.deviceListEditor: Optional[DeviceListEditor] = None
        self.blockListEditor: Optional[BlockListEditor] = None
        self.panelListEditor: Optional[PanelListEditor] = None
        self.imageListEditor: Optional[ImageListEditor] = None

        # reactivity
        self.view.selectProjectButton.clicked.connect(
            lambda: self.pathChangeRequested.emit()
        )
        self.model.pathChanged.connect(lambda: self.refresh())
        self.model.pathChanged.connect(lambda: self.validate())
        self.dataChanged.connect(lambda: self.validate())

        self.refresh()
        self.validate()

        # logging
        self.pathChangeRequested.connect(
            lambda: self.log.info("pathChangeRequested emitted"),
        )

    def refresh(self) -> None:
        if not self.model.isSet:
            return

        # update project editors
        # populate view using model
        self.deviceListEditor = DeviceListEditor(self.model)
        self.blockListEditor = BlockListEditor(self.model)
        self.panelListEditor = PanelListEditor(self.model)
        self.imageListEditor = ImageListEditor(self.model)

        self.view.updateView(
            deviceListView=self.deviceListEditor.view,
            blockListView=self.blockListEditor.view,
            panelListView=self.panelListEditor.view,
            imageListView=self.imageListEditor.view,
        )

        def updateTabStyle(editor: Editor):
            index = self.view.tabWidget.indexOf(editor.view)
            tabBar: QTabBar = self.view.tabWidget.tabBar()
            tabBar.setTabTextColor(
                index, Color.Black.qc() if editor.isValid else Color.Red.qc()
            )

        self.deviceListEditor.isValidChanged.connect(
            lambda: updateTabStyle(self.deviceListEditor)
        )
        self.blockListEditor.isValidChanged.connect(
            lambda: updateTabStyle(self.blockListEditor)
        )
        self.panelListEditor.isValidChanged.connect(
            lambda: updateTabStyle(self.panelListEditor)
        )
        updateTabStyle(self.deviceListEditor)
        updateTabStyle(self.blockListEditor)
        updateTabStyle(self.panelListEditor)

        self.deviceListEditor.deviceListChanged.connect(lambda: self.dataChanged.emit())
        self.blockListEditor.blockListChanged.connect(lambda: self.dataChanged.emit())
        self.panelListEditor.panelListChanged.connect(lambda: self.dataChanged.emit())

        # set project labels
        path: Path = self.model.path
        path: str = str(path.parent) if path else "none"

        name: str = self.model.name
        name: str = name if name else "none"

        self.view.setProjectLabels(path=path, name=name)

        # any subsequent changes in this widget are propagated to model; the rest of
        # the views handle their own changes
        self.view.descriptionTextEdit.setPlainText(self.model.state.description)

        def setDescriptionText():
            description = self.view.descriptionTextEdit.toPlainText()
            if self.model.state.description != description:
                self.model.state.description = description
                self.dataChanged.emit()

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

        isPanelListEditorValid = (
            self.panelListEditor.isValid if self.panelListEditor is not None else False
        )

        self.isValid = (
            isDeviceListEditorValid
            and isBlockListEditorValid
            and isPanelListEditorValid
            and self.model.isSet
        )

        self.log.info(f"validated to {str(self.isValid)}")
