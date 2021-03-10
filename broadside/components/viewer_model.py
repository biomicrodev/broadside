import logging
from pathlib import Path
from typing import Optional

from .state import State
from ..models.block import Block, Sample, Device, Vector
from ..models.image import Image
from ..models.panel import Panel, Channel
from ..models.payload import Formulation, Payload
from ..utils.events import EventEmitter


class ViewerModel:
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

    is_stale : bool
        Whether a save is pending or not. This is set to False by default, and whenever
        the project has been saved. If anything is changed, this is set to True.
    """

    log = logging.getLogger(__name__)

    class Events:
        def __init__(self):
            self.path = EventEmitter()
            self.is_stale = EventEmitter()

    def __init__(self):
        self.events = self.Events()

        self._is_stale = False
        self.state: Optional[State] = None
        # self.executors: Dict[str, Runner] = {}

        # self._images_loaded = False

        # logging
        self.events.is_stale.connect(
            lambda is_stale: self.log.debug(f"is_stale changed to {is_stale}")
        )
        self.events.path.connect(lambda path: self.log.debug(f"path changed to {path}"))

    @property
    def is_stale(self) -> bool:
        return self._is_stale

    @is_stale.setter
    def is_stale(self, val: bool) -> None:
        if self.is_stale is not val:
            self._is_stale = val
            self.events.is_stale.emit(val)

    @property
    def is_set(self) -> bool:
        return self.state is not None

    @property
    def path(self) -> Optional[Path]:
        return self.state.path if self.is_set else None

    @path.setter
    def path(self, val: Optional[Path]) -> None:
        """
        We don't change the project path until we get a response from the user, to make
        sure that any changes that must be saved are resolved.

        This is where the serialization from json to object happens. It's a bit messy,
        but this'll be enough for the scale we need.
        """
        if self.is_stale:
            self.log.warning(
                "Project setter called when stale; ensure controller checks `isStale` "
                "before setting"
            )
            return

        if val is None:
            self.log.debug("Project setter called with empty path; path unset")
            self.state = None
            # self.executors.clear()
            return

        if (self.is_set) and (self.path == val):
            self.log.debug("No change in path")
            return

        if not val.is_dir():
            self.log.warning(f"{str(val)} not a directory! Path not changed")
            return

        if val.name == "":
            self.log.warning(f"{str(val)} is base folder")
            return

        self._set_path(val)
        self.events.path.emit(val)

    def _set_path(self, val: Path) -> None:
        filepath = val / State.filename
        if not filepath.exists():
            self.is_stale = True

        self.state = State(path=val)
        self.state.events.description.connect(self._set_stale)

        # payload bindings
        self.state.payloads.events.changed.connect(self._set_stale)
        self.state.payloads.events.added.connect(
            lambda d: self._add_payload_bindings(d["item"])
        )
        self.state.payloads.events.added.connect(
            lambda d: self.log.debug(f'New payload "{d["item"].name}" added')
        )
        self.state.payloads.events.deleted.connect(
            lambda d: self.log.debug("Payload removed")
        )
        for payload in self.state.payloads:
            self._add_payload_bindings(payload)

        # block bindings
        self.state.blocks.events.changed.connect(self._set_stale)
        self.state.blocks.events.added.connect(
            lambda d: self._add_block_bindings(d["item"])
        )
        self.state.blocks.events.added.connect(
            lambda d: self.log.debug(f'New block "{d["item"].name}" added')
        )
        self.state.blocks.events.deleted.connect(
            lambda d: self.log.debug("Block removed")
        )
        for block in self.state.blocks:
            self._add_block_bindings(block)

        # panel bindings
        self.state.panels.events.changed.connect(self._set_stale)
        self.state.panels.events.added.connect(
            lambda d: self._add_panel_bindings(d["item"])
        )
        self.state.panels.events.added.connect(
            lambda d: self.log.debug(f'New panel "{d["item"].name}" added')
        )
        self.state.panels.events.deleted.connect(
            lambda d: self.log.debug("Panel removed")
        )
        for panel in self.state.panels:
            self._add_panel_bindings(panel)

        # image bindings
        for image in self.state.images:
            self._add_image_bindings(image)

    def _set_stale(self, *args, **kwargs):
        # for convenience
        self.is_stale = True

    def _add_payload_bindings(self, payload: Payload):
        payload.events.name.connect(self._set_stale)
        payload.events.ang_dir.connect(self._set_stale)
        payload.events.long_dir.connect(self._set_stale)
        payload.events.long_orient.connect(self._set_stale)
        payload.events.notes.connect(self._set_stale)

        # payload
        def add_formulation_bindings(formulation: Formulation):
            formulation.events.name.connect(self._set_stale)
            formulation.events.level.connect(self._set_stale)
            formulation.angle.events.value.connect(self._set_stale)

        payload.formulations.events.added.connect(
            lambda f: add_formulation_bindings(f["item"])
        )
        payload.formulations.events.changed.connect(self._set_stale)
        for formulation in payload.formulations:
            add_formulation_bindings(formulation)

    def _add_block_bindings(self, block: Block):
        block.events.name.connect(self._set_stale)
        block.events.notes.connect(self._set_stale)

        def add_sample_bindings(sample: Sample):
            sample.events.name.connect(self._set_stale)
            sample.cohorts.events.changed.connect(self._set_stale)

        block.samples.events.added.connect(lambda d: add_sample_bindings(d["item"]))
        block.samples.events.changed.connect(self._set_stale)
        for sample in block.samples:
            add_sample_bindings(sample)

        def add_device_bindings(device: Device):
            device.events.name.connect(self._set_stale)
            device.events.payload_name.connect(self._set_stale)
            device.events.sample_name.connect(self._set_stale)

        block.devices.events.added.connect(lambda d: add_device_bindings(d["item"]))
        block.devices.events.changed.connect(self._set_stale)
        for device in block.devices:
            add_device_bindings(device)

        def add_vector_bindings(vector: Vector):
            vector.pos.events.x.connect(self._set_stale)
            vector.pos.events.y.connect(self._set_stale)
            vector.angle.events.value.connect(self._set_stale)

        block.vectors.events.added.connect(lambda d: add_vector_bindings(d["item"]))
        for vector in block.vectors:
            add_vector_bindings(vector)

    def _add_panel_bindings(self, panel: Panel):
        panel.events.name.connect(self._set_stale)

        def add_channel_bindings(channel: Channel):
            channel.events.biomarker.connect(self._set_stale)
            channel.events.chromogen.connect(self._set_stale)
            channel.events.notes.connect(self._set_stale)

        panel.channels.events.added.connect(lambda d: add_channel_bindings(d["item"]))
        panel.channels.events.changed.connect(self._set_stale)
        for channel in panel.channels:
            add_channel_bindings(channel)

    def _add_image_bindings(self, image: Image):
        image.events.block_name.connect(self._set_stale)
        image.events.panel_name.connect(self._set_stale)

    def save(self) -> None:
        if not self.is_set:
            self.log.debug("No project path set, so not saving")
            return

        if not self.is_stale:
            self.log.debug("Up to date, so not saving")
            return

        self.state._save()
        self.is_stale = False

    def on_close(self):
        pass
