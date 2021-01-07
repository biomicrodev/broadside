import json
import logging
from pathlib import Path
from typing import List, Set

from .block import Block
from .device import Device, NO_DEVICE
from .image import read_images
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
    images_dir: str = "images"

    def __init__(self, path: Path):
        self.path = path

        # load only once
        filepath = self.path / self.filename
        if filepath.exists():
            try:
                with filepath.open("r") as file:
                    state = json.load(file)
                self.log.info(f"Project settings read from {str(filepath)}")
            except json.decoder.JSONDecodeError:
                state = {}
                self.log.info(f"Read settings failed; using default values")
        else:
            state = {}
            self.log.info("Project file not found; using default values")

        description = state.get("description", "")
        devices = [Device.from_dict(d) for d in state.get("devices", [])]
        blocks = [Block.from_dict(b) for b in state.get("blocks", [])]
        panels = [Panel.from_dict(p) for p in state.get("panels", [])]
        task_graph = TaskGraph.from_dict(state.get("task_graph", {}))

        # validate device names in samples
        device_names = [NO_DEVICE] + [d.name for d in devices]
        for block in blocks:
            for sample in block.samples:
                if sample.device_name not in device_names:
                    sample.device_name = ""

        self.description: str = description
        self.devices: List[Device] = devices
        self.blocks: List[Block] = blocks
        self.panels: List[Panel] = panels
        self.task_graph: TaskGraph = task_graph

        # derived properties
        self.images = read_images(filepath / self.images_dir)

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
            "task_graph": self.task_graph.as_dict(),
        }

        filepath = self.path / self.filename
        with filepath.open("w+") as file:
            json.dump(state, file, indent=2)
        self.log.info(f"Project settings saved to {str(filepath)}")

    def invalid_device_indexes(self) -> Set[int]:
        invalid: Set[int] = set(
            i for i, device in enumerate(self.devices) if not device.is_valid()
        )

        names = [device.name for device in self.devices]
        names_as_set = set(names)
        for name in names_as_set:
            indexes = [i for i, _name in enumerate(names) if _name == name]
            if len(indexes) > 1:
                invalid.update(indexes)

        return invalid

    def invalid_block_indexes(self) -> Set[int]:
        invalid: Set[int] = set(
            i for i, block in enumerate(self.blocks) if not block.is_valid()
        )

        names = [block.name for block in self.blocks]
        names_as_set = set(names)
        for name in names_as_set:
            indexes = [i for i, _name in enumerate(names) if _name == name]
            if len(indexes) > 1:
                invalid.update(indexes)

        for block_ind, block in enumerate(self.blocks):
            sample_names = [sample.name for sample in block.samples]
            sample_names_as_set = set(sample_names)
            for sample_name in sample_names_as_set:
                index_count = sample_names.count(sample_name)
                if index_count > 1:
                    invalid.add(block_ind)

        return invalid

    def invalid_panel_indexes(self) -> Set[int]:
        invalid: Set[int] = set(
            i for i, panel in enumerate(self.panels) if not panel.is_valid()
        )

        names = [panel.name for panel in self.panels]
        names_as_set = set(names)
        for name in names_as_set:
            indexes = [i for i, _name in enumerate(names) if _name == name]
            if len(indexes) > 1:
                invalid.update(indexes)

        return invalid

    def __repr__(self) -> str:
        return (
            f"State("
            f"description={self.description}, "
            f"devices={self.devices}, "
            f"blocks={self.blocks}, "
            f"panels={self.panels}, "
            f"task_graph={self.task_graph}"
            f")"
        )
