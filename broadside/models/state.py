import json
import logging
from pathlib import Path
from typing import List, Set, Optional, Any, Dict

from natsort import natsort_keygen

from .block import Block
from .device import Device, NO_DEVICE
from .image import Image, get_pr_image_relpaths
from .panel import Panel
from .task_graph import TaskGraph


class State:
    """
    path : pathlib.Path
        Path to project. The setter method does not set the path directly, since it is
        possible to want to set the path when there are pending saves. To hook up the
        logic for user interaction, the path setter will emit an event that the view
        must catch and handle. Upon resolution, the `_set_path` method sets the path.

    `description`, `devices`, `blocks`, `panels`, and `task_graph` are loaded as usual
    from the `project.json` file. The only odd one out is `images`, where `images` are
    loaded from the `project.json` file, and any filepaths in the `images` folder that
    are new are added.
    """

    log = logging.getLogger(__name__)

    filename: str = "project.json"

    def __init__(self, path: Path):
        self.path = path

        # load only once
        filepath = path / self.filename
        if filepath.exists():
            try:
                with filepath.open("r") as file:
                    state = json.load(file)
                self.log.info(f"Project settings read from {str(filepath)}")
            except json.decoder.JSONDecodeError:
                state = {}
                self.log.info("Read settings failed; using default values")
        else:
            state = {}
            self.log.info("Project file not found; using default values")

        # load from dictionary
        description = state.get("description", "")
        devices = [Device.from_dict(d) for d in state.get("devices", [])]
        blocks = [Block.from_dict(b) for b in state.get("blocks", [])]
        panels = [Panel.from_dict(p) for p in state.get("panels", [])]
        images = self._get_images(state.get("images", []))
        task_graph = TaskGraph.from_dict(state.get("task_graph", {}))

        self.description = description
        self.devices = devices
        self.blocks = blocks
        self.panels = panels
        self.images = images
        self.task_graph = task_graph

        self.validate()

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
            "images": [i.as_dict() for i in self.images],
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

        # check if device names are not empty strings
        for block_ind, block in enumerate(self.blocks):
            for sample in block.samples:
                device_name = sample.device_name
                if device_name == "":
                    invalid.add(block_ind)
                    break

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

    def _get_images(self, state_images: List[Dict[str, Any]]) -> List[Image]:
        fs_relpaths: List[Path] = get_pr_image_relpaths(self.path)

        images: List[Image] = []

        for im in state_images:
            im: Dict[str, Any]
            try:
                pr_image: Image = Image.from_dict(im)
            except RuntimeError:
                # image is in an invalid state
                continue

            # all good
            if pr_image.exists(self.path):
                images.append(pr_image)
                continue

            # otherwise, it could have been moved elsewhere (same filename)
            fs_relpath: Optional[Path] = next(
                (rp for rp in fs_relpaths if rp.name == pr_image.relpath.name),
                None,
            )
            if fs_relpath is None:
                self.log.warning(f"Unable to find {pr_image.relpath}")
                continue

            # :O it was indeed moved elsewhere
            self.log.info(f"{pr_image.relpath} moved to {fs_relpath}")
            fs_relpaths.remove(fs_relpath)
            pr_image.relpath = fs_relpath  # set new relpath
            images.append(pr_image)

        existing_relpaths: List[Path] = [i.relpath for i in images]
        new_fs_images: List[Image] = [
            Image.from_dict({"relpath": relpath})
            for relpath in fs_relpaths
            if relpath not in existing_relpaths
        ]
        images.extend(new_fs_images)
        images = sorted(images, key=natsort_keygen(key=lambda im: im.relpath))

        return images

    def validate(self) -> None:
        # validate device names in samples
        device_names = [NO_DEVICE] + [d.name for d in self.devices]
        for block in self.blocks:
            for sample in block.samples:
                if sample.device_name not in device_names:
                    sample.device_name = ""

        # validate block and panel names in images
        block_names = [b.name for b in self.blocks]
        panel_names = [p.name for p in self.panels]
        for image in self.images:
            if image.block_name not in block_names:
                image.block_name = ""
            if image.panel_name not in panel_names:
                image.panel_name = ""

    def __repr__(self) -> str:
        return (
            "State("
            f"description={self.description}, "
            f"devices={self.devices}, "
            f"blocks={self.blocks}, "
            f"panels={self.panels}, "
            f"images={self.images}, "
            f"task_graph={self.task_graph}"
            ")"
        )
