import logging
from pathlib import Path
from typing import Optional, Dict

from qtpy.QtGui import QColor
from qtpy.QtWidgets import QTabBar

from .blocks import BlocksEditor
from .images import ImagesEditor
from .panels import PanelsEditor
from .payloads import PayloadsEditor
from .view import ProjectView
from .. import Step
from ...editor import Editor
from ...viewer_model import ViewerModel
from ....utils.colors import Color
from ....utils.events import EventEmitter


class ProjectStep(Step):
    log = logging.getLogger(__name__)

    name = "Project"

    class Events(Step.Events):
        def __init__(self):
            super().__init__()
            self.path_request = EventEmitter()

    def __init__(self, model: ViewerModel):
        super().__init__()

        self.events = self.Events()
        self.events.path_request.connect(
            lambda _: self.log.info("path change requested")
        )

        self.model = model
        self._view = ProjectView()

        # editors
        self.editors: Optional[Dict[str, Editor]] = None

        # reactivity
        self._view.selectProjectButton.clicked.connect(
            lambda _: self.events.path_request.emit()
        )
        self.model.events.path.connect(lambda _: self.refresh())
        self.model.events.path.connect(lambda _: self.validate())

        self.refresh()
        self.validate()

    def refresh(self) -> None:
        if not self.model.is_set:
            return

        # set up editors
        self.editors = {
            "payloads": PayloadsEditor(self.model),
            "blocks": BlocksEditor(self.model),
            # "panels": PanelsEditor(self.model),
            # "images": ImagesEditor(self.model),
        }

        self._view.updateEditors(
            payloadsView=self.editors["payloads"]._view,
            blocksView=self.editors["blocks"]._view,
            # panelsView=self.editors["panels"]._view,
            # imagesView=self.editors["images"]._view,
        )

        def update_tab_style(editor: Editor):
            index = self._view.tabWidget.indexOf(editor._view)
            tab_bar: QTabBar = self._view.tabWidget.tabBar()
            tab_bar.setTabTextColor(
                index, QColor(*(Color.Black if editor.is_valid else Color.Red).value)
            )

        # whenever any editor changes validation, update project's validation
        for n in self.editors.keys():
            self.editors[n].events.is_valid.connect(
                lambda _: update_tab_style(self.editors[n])
            )
            update_tab_style(self.editors[n])
            self.editors[n].events.is_valid.connect(
                lambda _: self.events.is_valid.emit()
            )

        # set project labels; model is guaranteed to be set here
        path: Path = self.model.path
        path: str = str(path.parent) if path else "none"

        name: str = self.model.path.name
        name: str = name if name else "none"

        self._view.setProjectLabels(path=path, name=name)
        self._view.descriptionTextEdit.setPlainText(self.model.state.description)

        def set_description():
            description = self._view.descriptionTextEdit.toPlainText()
            self.model.state.description = description

        self._view.descriptionTextEdit.textChanged.connect(set_description)

    def validate(self) -> None:
        if not self.model.is_set:
            self.is_valid = False
        else:
            self.model.state.validate()
            self.is_valid = all(editor.is_valid for editor in self.editors.values())
