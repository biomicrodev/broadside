import json
import logging
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List

from PySide2.QtCore import QObject, Signal

from . import QStaleableObject
from .device import Device


class SaveAction(Enum):
    Save = "SAVE"
    Cancel = "CANCEL"
    Discard = "DISCARD"


class Block:
    pass


class Image:
    pass


class ProjectModel(QStaleableObject):
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
    askSave = Signal(Path)
    projectChanged = Signal()

    def __init__(self, parent: QObject = None):
        super().__init__(parent=parent)

        self._path: Optional[Path] = None
        self._name = ""
        self._description = ""
        self._blocks: List[Block] = []
        self._devices: List[Device] = []
        self._images: List[Image] = []
        self._taskGraph = {}

        self._logEvents()

    def _logEvents(self):
        self.askSave.connect(lambda: self.log.info("askSave emitted"))
        self.projectChanged.connect(
            lambda: self.log.info(f"projectChanged to {self._path}")
        )
        self.isStaleChanged.connect(lambda: self.log.info("isStale emitted"))

    @property
    def path(self) -> Path:
        return self._path

    @path.setter
    def path(self, val: Optional[Path]) -> None:
        if not val or str(val) == "":
            self.log.info("Project setter called with empty path; path not changed")
            return

        if self.path is None:
            # no currently active project, so just set path
            self._setPath(val)
            self._read()

        elif self.path == val:
            self.log.info("No change in path")

        elif not val.is_dir():
            self.log.warning(f"{str(self.path)} not a directory! Path not changed")

        elif self.isStale:
            self.askSave.emit(val)

        else:
            self._setPath(val)
            self._read()

    def _setPath(self, val: Path) -> None:
        """
        We don't change the project path until we get a response from the user, to make
        sure that any changes that must be saved are resolved.
        """
        self._path = val
        self._name = val.name

        self.projectChanged.emit()

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, val: str) -> None:
        self._description = val
        self.isStale = True

    @property
    def blocks(self) -> List[Block]:
        return self._blocks

    @blocks.setter
    def blocks(self, val: List[Block]) -> None:
        self._blocks = val
        # TODO: is this the right way? probably not.

    @property
    def devices(self) -> List[Device]:
        return self._devices

    @devices.setter
    def devices(self, val: List[Device]) -> None:
        self._devices = val

    def onSaveResponse(self, *, newPath: Path, action: SaveAction) -> None:
        if action == SaveAction.Cancel:
            self.log.info("Project settings save cancelled")
            pass

        elif action == SaveAction.Save:
            self.log.info("Project settings saved")
            self.save()
            self._setPath(newPath)
            self._read()

            self.isStale = False

        elif action == SaveAction.Discard:
            self.log.info("Project settings discarded")
            # do not save here
            self._setPath(newPath)
            self._read()

            self.isStale = False

        else:
            raise RuntimeError(f"Unknown action {str(action)}")

    def _read(self) -> None:
        filepath = self.path / self.filename

        settings = {}
        if filepath.exists():
            with open(str(filepath), "r") as file:
                settings = json.load(file)

            self.log.info(f"Settings read from {str(filepath)}")
        else:
            self.log.info("Settings file not found")

        self._description = settings.get("description", "")

    def save(self) -> None:
        if self.path is None:
            self.log.info("Path is none, so not saving")
            return

        settings = {
            "name": self.name,
            "description": self.description,
        }

        filepath = self.path / self.filename
        with open(str(filepath), "w+") as file:
            json.dump(settings, file, indent=2)

        self.isStale = False

        self.log.info(f"Settings saved to {str(filepath)}")

    def as_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "name": self.name,
            "isStale": self.isStale,
            "description": self.description,
        }

    def __str__(self) -> str:
        return str(self.as_dict())
