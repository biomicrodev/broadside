import json
import logging
from pathlib import Path
from typing import List, Set, Optional, Any, Dict

from natsort import natsort_keygen

from ..models.block import Block
from ..models.image import Image, get_pr_image_relpaths
from ..models.panel import Panel
from ..models.payload import Payload
from ..models.task_graph import TaskGraph
from ..utils.events import EventedList, EventEmitter


class State:
    """
    path : pathlib.Path
        Path to project. The setter method does not set the path directly, since it is
        possible to want to set the path when there are pending saves. To hook up the
        logic for user interaction, the path setter will emit an event that the view
        must catch and handle. Upon resolution, the `_set_path` method sets the path.

    `description`, `payloads`, `blocks`, `panels`, and `task_graph` are loaded as usual
    from the `project.json` file. The only odd one out is `images`, where `images` are
    loaded from the `project.json` file, and any filepaths in the `images` folder that
    are new are added.
    """

    log = logging.getLogger(__name__)

    filename: str = "project.json"

    class Events:
        def __init__(self):
            self.description = EventEmitter()

    def __init__(self, *, path: Path):
        self.path = path

        # set up events
        self.events = self.Events()

        # load only once
        filepath = path / self.filename
        if filepath.exists():
            try:
                with filepath.open("r") as file:
                    state = json.load(file)
                self.log.debug(f"Project settings read from {str(filepath)}")
            except json.decoder.JSONDecodeError:
                state = {}
                self.log.warning("Read settings failed; using default values")
        else:
            state = {}
            self.log.debug("Project file not found; using default values")

        # load from dictionary
        self._description = state.get("description", "")

        self._payloads = EventedList(
            [Payload.from_dict(d) for d in state.get("payloads", [])]
        )
        self._blocks = EventedList(
            [Block.from_dict(b) for b in state.get("blocks", [])]
        )
        self._panels = EventedList(
            [Panel.from_dict(p) for p in state.get("panels", [])]
        )

        self._images = self._get_images(state.get("images", []))
        self._task_graph = TaskGraph.from_dict(state.get("task_graph", {}))

        self.validate()

    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, val: str) -> None:
        if self.description != val:
            self._description = val
            self.events.description.emit(val)

    @property
    def payloads(self) -> EventedList[Payload]:
        return self._payloads

    @property
    def blocks(self) -> EventedList[Block]:
        return self._blocks

    @property
    def panels(self) -> EventedList[Panel]:
        return self._panels

    @property
    def images(self) -> List[Image]:
        return self._images

    @property
    def task_graph(self) -> TaskGraph:
        return self._task_graph

    def _save(self) -> None:
        """
        'name' is included in the file to help identify the file without having to find
        the parent folder.
        """
        state = {
            "name": self.path.name,
            "description": self.description,
            "payloads": [d.as_dict() for d in self.payloads],
            "blocks": [b.as_dict() for b in self.blocks],
            "panels": [p.as_dict() for p in self.panels],
            "images": [i.as_dict() for i in self.images],
            "task_graph": self.task_graph.as_dict(),
        }

        filepath = self.path / self.filename
        with filepath.open("w+") as file:
            json.dump(state, file, indent=2)
        self.log.debug(f"Project settings saved to {str(filepath)}")

    def invalid_payload_indexes(self) -> Set[int]:
        invalid: Set[int] = set(
            i for i, payload in enumerate(self.payloads) if not payload.is_valid()
        )

        # payload name duplicates
        names = [payload.name for payload in self.payloads]
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

        # block name duplicates
        names = [block.name for block in self.blocks]
        names_as_set = set(names)
        for name in names_as_set:
            indexes = [i for i, _name in enumerate(names) if _name == name]
            if len(indexes) > 1:
                invalid.update(indexes)

        # sample name duplicates
        for block_ind, block in enumerate(self.blocks):
            sample_names = [sample.name for sample in block.samples]
            sample_names_as_set = set(sample_names)
            for sample_name in sample_names_as_set:
                index_count = sample_names.count(sample_name)
                if index_count > 1:
                    invalid.add(block_ind)

        # check if device names are not empty strings
        for block_ind, block in enumerate(self.blocks):
            for device in block.devices:
                if device.name == "":
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

    def invalid_image_indexes(self) -> Set[int]:
        invalid: Set[int] = set()
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
                (
                    relpath
                    for relpath in fs_relpaths
                    if relpath.name == pr_image.relpath.name
                ),
                None,
            )
            if fs_relpath is None:
                self.log.warning(f"Unable to find {pr_image.relpath}")
                continue

            # :O it was indeed moved elsewhere
            self.log.debug(f"{pr_image.relpath} moved to {fs_relpath}")
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
        pass
        # validate device names in samples
        # device_names = [NO_DEVICE] + [d.name for d in self.devices]
        # for block in self.blocks:
        #     for sample in block.samples:
        #         if sample.device_name not in device_names:
        #             sample.device_name = ""

        # validate block and panels names in images
        # block_names = [b.name for b in self.blocks]
        # panel_names = [p.name for p in self.panels]
        # for image in self.images:
        #     if image.block_name not in block_names:
        #         image.block_name = ""
        #     if image.panel_name not in panel_names:
        #         image.panel_name = ""

    def __repr__(self) -> str:
        return (
            "State("
            f"description={self.description}, "
            f"payloads={self.payloads}, "
            f"blocks={self.blocks}, "
            f"panels={self.panels}, "
            f"images={self.images}, "
            f"task_graph={self.task_graph}"
            ")"
        )
