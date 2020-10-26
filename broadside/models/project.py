import enum
import json
import os
import pprint
import warnings
from typing import List, Dict, Any

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
    filename : str
        Filename of project settings. It's recommended to keep the default filename.

    Attributes
    ----------
    path : str
        Path to project. The setter method does not set the path directly, since it is
        possible to want to set the path when there are pending saves. To hook up the
        logic for user interaction, the path setter will emit an event that the view
        must catch and handle. Upon resolution, the `_set_path` method sets the path.

    name : str
        Name of project; read-only. This is set when the path is set, and is assigned
        the basename of the project path.

    pending_save : bool
        Whether a save is pending or not. This is set to False by default, and whenever
        the project has been saved. If anything is changed, this is set to True.

    description : str
        Project description.

    panels : List[]

    devices : List[]

    image_groups : List[]

    task_graph : Dict[str, ...]

    """

    def __init__(self):
        self._filename = "project.json"

        self._path = ""
        self._name = ""
        self._pending_save = False
        self._description = ""
        self._panels = []
        self._devices = []
        self._image_groups = []
        self._task_graph = {}

        self.events = EmitterGroup(
            source=self,
            auto_connect=True,
            ask_save=Event,
            description=Event,
            panels=Event,
            devices=Event,
            image_groups=Event,
            task_graph=Event,
            pending_save=Event,
            title=Event,
        )

        self.init_reactivity()

    def init_reactivity(self) -> None:
        # whenever anything is changed, the project becomes stale and a save is pending
        def pending_save(event: Event):
            self.pending_save = True

        self.events.description.connect(pending_save)
        self.events.panels.connect(pending_save)
        self.events.devices.connect(pending_save)
        self.events.image_groups.connect(pending_save)
        self.events.task_graph.connect(pending_save)

        self.events.pending_save.connect(lambda event: self.events.title())

    @property
    def filename(self) -> str:
        """
        The filename should be the default value of `project.json` to avoid conflicts.
        """
        return self._filename

    @property
    def path(self) -> str:
        return self._path

    @path.setter
    def path(self, val: str) -> None:
        if not val:
            print("Project setter called with empty path; path not changed")
            return

        if self.path == "":
            # no currently active project
            self._set_path(val)

        elif self.path == val:
            # no change in project
            print("No change in path")

        elif not os.path.isdir(val):
            print(f"{self.path} not a directory! Path not changed")

        else:
            self.events.ask_save(new_path=val)

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
        self.events.pending_save()

    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, val: str) -> None:
        self._description = val
        self.pending_save = True

    @property
    def panels(self) -> List:
        return self._panels

    @panels.setter
    def panels(self, val: List) -> None:
        self._panels = val
        self.events.panels()

    @property
    def devices(self) -> List:
        return self._devices

    @devices.setter
    def devices(self, val: List) -> None:
        self._devices = val
        self.events.devices()

    @property
    def image_groups(self) -> List:
        return self._image_groups

    @image_groups.setter
    def image_groups(self, val: List) -> None:
        self._image_groups = val
        self.events.image_groups()

    @property
    def task_graph(self) -> Dict:
        return self._task_graph

    @task_graph.setter
    def task_graph(self, val: Dict) -> None:
        self._task_graph = val
        self.events.task_graph()

    def on_save_response(self, *, new_path: str, action: SaveAction) -> None:
        if action == SaveAction.Cancel:
            pass

        elif action == SaveAction.Save:
            self.save()
            self._set_path(new_path)
            self._read()

        elif action == SaveAction.Discard:
            # do not save here
            self._set_path(new_path)
            self._read()

            self.pending_save = False

        else:
            raise RuntimeError(f"Unknown action {str(action)}")

    def _read(self) -> None:
        filepath = os.path.join(self.path, self._filename)

        settings = {}
        if os.path.exists(filepath):
            with open(filepath, "r") as file:
                settings = json.load(file)

        self.description = settings.get("description", "")
        self.panels = settings.get("panels", [])
        self.devices = settings.get("devices", [])
        self.image_groups = settings.get("image_groups", [])
        self.task_graph = settings.get("task_graph", {})

    def save(self) -> None:
        settings = {
            "name": self.name,
            "description": self.description,
            "panels": self.panels,
            "devices": self.devices,
            "image_groups": self.image_groups,
            "task_graph": self.task_graph,
        }

        filepath = os.path.join(self.path, self._filename)
        with open(filepath, "w+") as file:
            json.dump(settings, file, indent=2)

        self.pending_save = False

    @property
    def state(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "name": self.name,
            "description": self.description,
            "images": [],
            "image_groups": self.image_groups,
            "panels": self.panels,
            "devices": self.devices,
            "task_graph": self.task_graph,
            "pending_save": self.pending_save,
        }

    def __str__(self) -> str:
        return pprint.pformat(self.state, indent=2, sort_dicts=False)
