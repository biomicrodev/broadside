import json
import pprint
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List

from PySide2.QtCore import QObject, Signal

from broadside.gui.models import QStaleableObject
from broadside.gui.models.device import Device


class SaveAction(Enum):
    Save = "SAVE"
    Cancel = "CANCEL"
    Discard = "DISCARD"


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

    filename = "project.json"

    # model to view
    askSave = Signal(Path)
    askTitleUpdate = Signal()

    def __init__(self, parent: QObject = None):
        super().__init__(parent=parent)

        self._path: Optional[Path] = None
        self._name = ""
        self._description = ""
        self._panels: List[Panel] = []
        self._devices: List[Device] = []
        self._imageGroups: List[ImageGroup] = []
        self._taskGraph = {}

        self.isStaleChanged.connect(self.askTitleUpdate.emit)

    @property
    def path(self) -> Path:
        return self._path

    @path.setter
    def path(self, val: Optional[Path]) -> None:
        if not val:
            print("Project setter called with empty path; path not changed")
            return

        if self.path is None:
            # no currently active project
            self._setPath(val)

        elif self.path == val:
            # no change in project
            print("No change in path")

        elif not val.is_dir():
            print(f"{str(self.path)} not a directory! Path not changed")

        else:
            self.askSave.emit(val)

    def _setPath(self, val: Path) -> None:
        """
        We don't change the project path until we get a response from the user, to make
        sure that any changes that must be saved are resolved.
        """
        self._path = val
        self._name = val.name

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
    def panels(self) -> List[Panel]:
        return self._panels

    @panels.setter
    def panels(self, val: List[Panel]) -> None:
        if self.panels != val:
            self._panels = val
            self.isStale = True

    def onSaveResponse(self, *, newPath: Path, action: SaveAction) -> None:
        if action == SaveAction.Cancel:
            pass

        elif action == SaveAction.Save:
            self.save()
            self._setPath(newPath)
            self._read()

            self.isStale = False

        elif action == SaveAction.Discard:
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

        self.description = settings.get("description", "")

    def save(self) -> None:
        settings = {
            "name": self.name,
            "description": self.description,
        }

        filepath = self.path / self.filename
        with open(str(filepath), "w+") as file:
            json.dump(settings, file, indent=2)

        self.isStale = False

    def as_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "name": self.name,
            "isStale": self.isStale,
            "description": self.description,
        }

    def __str__(self) -> str:
        return pprint.pformat(self.as_dict, indent=2, sort_dicts=False)
