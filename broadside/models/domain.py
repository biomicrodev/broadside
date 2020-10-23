import enum
import json
import os
import warnings

from napari.utils.events import EmitterGroup, Event


class SaveAction(enum.Enum):
    Save = "SAVE"
    Cancel = "CANCEL"
    Discard = "DISCARD"


class ProjectModel:
    """
    Model containing domain logic, including workflow management.

    Parameters
    ----------
    path : str
        Path to the project folder
    filename : str
        Filename of project settings. It's recommended to keep the default filename.

    Attributes
    ----------
    """

    def __init__(self, *, filename: str = "project.json"):
        if filename != "project.json":
            warnings.warn(
                """\
We recommend that you keep the default filename, to avoid potential conflicts with 
other filenames in the future.
"""
            )

        self._path = ""
        self._name = ""
        self._pending_save = False
        self._description = ""
        self._panels = []
        self._devices = []
        self._image_groups = []
        self._task_graph = {}

        self.events = EmitterGroup(source=self, auto_connect=True, ask_save=Event,)

        self.filename = filename

    @property
    def path(self) -> str:
        return self._path

    @path.setter
    def path(self, val: str) -> None:
        if val and (self.path != val):
            # emit signal to interact with user if unsaved
            pass

        elif not os.path.isdir(val):
            print(f"{self.path} not a directory! Path not changed")

        else:
            print("Project setter called; path not changed")

    def _set_path(self, val: str) -> None:
        """
        We don't change the project path until we get a response from the user, to make
        sure that any changes that must be saved are resolved.
        """
        self._path = val
        self._name = os.path.basename(val)

    @property
    def name(self) -> str:
        return self._name

    @property
    def pending_save(self) -> bool:
        return self._pending_save

    @pending_save.setter
    def pending_save(self, val: bool) -> None:
        self._pending_save = val

    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, val: str) -> None:
        self._description = val
        self.pending_save = True

    def on_save_request(self, *, new_path: str, action: SaveAction) -> None:
        if action == SaveAction.Cancel:
            return

        elif action == SaveAction.Save:
            self._save()
            self._set_path(new_path)
            self._read()

            self._pending_save = False

        elif action == SaveAction.Discard:
            # do not save here
            self._set_path(new_path)
            self._read()

            self._pending_save = False

        else:
            raise RuntimeError(f"Unknown action {str(action)}")

    def _read(self) -> None:
        filepath = os.path.join(self.path, self.filename)
        if not os.path.exists(filepath):
            return

        with open(filepath, "r") as file:
            settings = json.load(file)

        self.description = settings.get("description", "")
        self.panels = settings.get("panels", [])
        self.devices = settings.get("devices", [])
        self.image_groups = settings.get("image_groups", [])

    def _save(self) -> None:
        settings = {
            "name": self.name,
            "description": self.description,
            "image_groups": [],
            "panels": [],
            "devices": [],
            "task_graph": None,
        }

        filepath = os.path.join(self.path, self.filename)
        with open(filepath, "w+") as file:
            json.dump(settings, file, indent=2)

    def __str__(self) -> str:
        properties = {
            "path": self.path,
            "name": self.name,
            "description": self.description,
            "images": "\n\t".join([]),
            "image_groups": "\n\t".join(self.image_groups),
            "panels": "\n\t".join([]),
            "devices": "\n\t".join([]),
            "task_graph": None,
            "pending_save": self.pending_save,
        }

        return "\n".join(f"{key}: {value}" for key, value in properties.items())
