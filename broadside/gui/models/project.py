import json
import logging
from enum import Enum
from pathlib import Path
from typing import Optional, List

from PySide2.QtCore import Signal, QObject

from .block import Block
from .device import Device
from .image import Image


class SaveAction(Enum):
    Save = "SAVE"
    Cancel = "CANCEL"
    Discard = "DISCARD"


class ProjectModel(QObject):
    """
    Model containing domain logic, including workflow management.

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

    filename = "project.json"

    # model to view
    pathChanged = Signal()
    isStaleChanged = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._isStale = False

        self._path: Optional[Path] = None
        self._name = ""
        self._description = ""
        self._devices: List[Device] = []
        self._blocks: List[Block] = []
        self._images: List[Image] = []
        self._taskGraph = {}

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
    def path(self) -> Path:
        return self._path

    @path.setter
    def path(self, val: Optional[Path]) -> None:
        if (not val) or (str(val) == ""):
            self.log.info("Project setter called with empty path; path not changed")
            return

        if self.path is None:
            # no currently active project, so just set path
            self._updatePath(val)

        elif self.path == val:
            self.log.info("No change in path")

        elif not val.is_dir():
            self.log.warning(f"{str(self.path)} not a directory! Path not changed")

        elif self.isStale:
            self.log.warning(
                "Project setter called when stale; ensure controller checks before setting"
            )

        else:
            self._updatePath(val)

    def _updatePath(self, newPath: Path) -> None:
        """
        We don't change the project path until we get a response from the user, to make
        sure that any changes that must be saved are resolved.

        This is where the serialization from json to object happens. It's a bit messy,
        but this'll be enough for the scale we need.
        """
        self._path = newPath
        self._name = newPath.name

        filepath = self.path / self.filename

        settings = {}
        if filepath.exists():
            with open(str(filepath), "r") as file:
                settings = json.load(file)

            self.log.info(f"Settings read from {str(filepath)}")
        else:
            self.log.info("Settings file not found; values set to default")

        self._description = settings.get("description", "")
        self._devices = [Device.from_dict(d) for d in settings.get("devices", [])]
        self._blocks = [Block.from_dict(s) for s in settings.get("blocks", [])]

        self.pathChanged.emit()

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, val: str) -> None:
        if self.description != val:
            self._description = val
            self.isStale = True

    @property
    def devices(self) -> List[Device]:
        return self._devices

    @property
    def blocks(self) -> List[Block]:
        return self._blocks

    def save(self) -> None:
        """
        This is where the serialization from object to json happens.
        """
        if self.path is None:
            self.log.info("Path is none, so not saving")
            return

        if not self.isStale:
            self.log.info("Up to date, so not saving")
            return

        settings = {
            "name": self.name,
            "description": self.description,
            "devices": [d.as_dict() for d in self.devices],
            "blocks": [s.as_dict() for s in self.blocks],
        }

        filepath = self.path / self.filename
        with filepath.open("w+") as file:
            json.dump(settings, file, indent=2)

        self.isStale = False

        self.log.info(f"Settings saved to {str(filepath)}")
