import logging
from pathlib import Path
from typing import Optional, List

from PySide2.QtCore import QObject, Signal

from ..models.block import Block
from ..models.device import Device
from ..models.panel import Panel
from ..models.state import State
from ..models.task_graph import TaskGraph


class ViewerModel(QObject):
    """
    Parameters
    ----------
    filename : str
        Filename of project settings. It's recommended to keep the default filename.

    Attributes
    ----------
    path : pathlib.Path
        Path to project. The setter method does not set the path directly, since it is
        possible to want to set the path when there are pending saves. To hook up the
        logic for user interaction, the path setter will emit an event that the view
        must catch and handle. Upon resolution, the `_set_path` method sets the path.

    name : str
        Name of project; read-only. This is set when the path is set, and is assigned
        the basename of the project path.

    isStale : bool
        Whether a save is pending or not. This is set to False by default, and whenever
        the project has been saved. If anything is changed, this is set to True.

    description : str
        Project description.
    """

    log = logging.getLogger(__name__)

    # model to view
    pathChanged = Signal()
    isStaleChanged = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._isStale = False
        self.state: Optional[State] = None

        # logging
        self.isStaleChanged.connect(lambda: self.log.info("isStaleChanged emitted"))
        self.pathChanged.connect(lambda: self.log.info("pathChanged emitted"))

    @property
    def isStale(self) -> bool:
        return self._isStale

    @isStale.setter
    def isStale(self, val: bool) -> None:
        if self.isStale is not val:
            self._isStale = val
            self.isStaleChanged.emit()

    @property
    def isSet(self) -> bool:
        return self.state is not None

    @property
    def name(self) -> Optional[str]:
        return self.state.path.name if self.isSet else None

    @property
    def path(self) -> Optional[Path]:
        return self.state.path if self.isSet else None

    @path.setter
    def path(self, val: Optional[Path]) -> None:
        """
        We don't change the project path until we get a response from the user, to make
        sure that any changes that must be saved are resolved.

        This is where the serialization from json to object happens. It's a bit messy,
        but this'll be enough for the scale we need.
        """
        if self.isStale:
            self.log.warning(
                "Project setter called when stale; ensure controller checks `isStale` "
                "before setting"
            )
            return

        if val is None:
            self.log.info("Project setter called with empty path; path unset")
            self.state = None
            return

        if (self.isSet) and (self.path == val):
            self.log.info("No change in path")
            return

        if not val.is_dir():
            self.log.warning(f"{str(val)} not a directory! Path not changed")
            return

        if val.name == "":
            self.log.warning(f"{str(val)} is base folder")
            return

        self.state = State(val)
        self.pathChanged.emit()

    @property
    def description(self) -> Optional[str]:
        return self.state.description if self.isSet else None

    @description.setter
    def description(self, val: str) -> None:
        if self.isSet and (self.description != val):
            self.state.description = val
            self.isStale = True

    @property
    def devices(self) -> List[Device]:
        return self.state.devices if self.isSet else []

    @property
    def blocks(self) -> List[Block]:
        return self.state.blocks if self.isSet else []

    @property
    def panels(self) -> List[Panel]:
        return self.state.panels if self.isSet else []

    @property
    def task_graph(self) -> Optional[TaskGraph]:
        return self.state.task_graph if self.isSet else None

    def save(self) -> None:
        if not self.isSet:
            self.log.info("No project path set, so not saving")
            return

        if not self.isStale:
            self.log.info("Up to date, so not saving")
            return

        self.state.save()
        self.isStale = False
