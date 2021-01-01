import json
import logging
from pathlib import Path

from .block import Block
from .device import Device
from .panel import Panel
from .task_graph import TaskGraph


class State:
    """
    path : pathlib.Path
        Path to project. The setter method does not set the path directly, since it is
        possible to want to set the path when there are pending saves. To hook up the
        logic for user interaction, the path setter will emit an event that the view
        must catch and handle. Upon resolution, the `_set_path` method sets the path.
    """

    log = logging.getLogger(__name__)

    filename: str = "project.json"

    def __init__(self, path: Path):
        self.path = path

        # load only once
        filepath = self.path / self.filename
        state = {}
        if filepath.exists():
            with filepath.open("r") as file:
                state = json.load(file)
            self.log.info(f"Project settings read from {str(filepath)}")
        else:
            self.log.info("Project file not found; using default values")

        description = state.get("description", "")
        devices = [Device.from_dict(d) for d in state.get("devices", [])]
        blocks = [Block.from_dict(b) for b in state.get("blocks", [])]
        panels = [Panel.from_dict(p) for p in state.get("panels", [])]
        task_graph = TaskGraph.from_dict(state.get("task_graph", {}))

        self.description = description
        self.devices = devices
        self.blocks = blocks
        self.panels = panels
        self.task_graph = task_graph

        # derived properties
        images = []
        self.images = images

    def save(self) -> None:
        """
        'name' is included in the file to help identify the file without having to find
        the parent folder.
        """
        state = {
            "name": self.path.name,
            "description": self.description,
            "devices": [d.as_dict() for d in self.devices],
            "blocks": [b.as_dict() for b in self.blocks],
            "panels": [p.as_dict() for p in self.panels],
            "task_graph": self.task_graph,
        }

        filepath = self.path / self.filename
        with filepath.open("w+") as file:
            json.dump(state, file, indent=2)

        self.log.info(f"Project settings saved to {str(filepath)}")
