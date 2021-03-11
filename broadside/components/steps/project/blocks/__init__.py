import logging
from typing import Set

from qtpy.QtCore import Qt
from qtpy.QtGui import QColor
from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabBar,
    QScrollArea,
    QMessageBox,
    QSplitter,
)

from .block_diagrams import BlockDiagramEditorView, BlockDiagramEditor
from .devices import DevicesEditor, DevicesEditorView
from .samples import SamplesEditor, SamplesEditorView
from ....editor import Editor
from ....utils import EditableTabWidget, showYesNoDialog
from ....viewer_model import ViewerModel
from .....models.block import Block, Sample, Device
from .....utils.colors import Color


class BlockEditorView(QWidget):
    def __init__(
        self,
        *args,
        samplesEditorView: SamplesEditorView,
        devicesEditorView: DevicesEditorView,
        blockDiagramEditorView: BlockDiagramEditorView,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        splitter = QSplitter()
        splitter.setOrientation(Qt.Horizontal)
        splitter.addWidget(samplesEditorView)
        splitter.addWidget(devicesEditorView)
        splitter.addWidget(blockDiagramEditorView)
        splitter.setHandleWidth(8)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 1)
        splitter.setChildrenCollapsible(False)
        splitter.setContentsMargins(0, 0, 0, 0)
        splitter.setSizes([2000, 2000, 2000])

        scrollArea = QScrollArea()
        scrollArea.setWidget(splitter)
        scrollArea.setWidgetResizable(True)

        parentLayout = QVBoxLayout()
        parentLayout.addWidget(scrollArea, 1)
        self.setLayout(parentLayout)


class BlocksEditorView(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.tabWidget = EditableTabWidget(addButtonText="Add new block")

        layout = QVBoxLayout()
        layout.addWidget(self.tabWidget)
        self.setLayout(layout)

    def styleInvalidTabs(self, indexes: Set[int]) -> None:
        tabBar: QTabBar = self.tabWidget.tabBar()
        for index in range(tabBar.count()):
            color = Color.Red if index in indexes else Color.Black
            tabBar.setTabTextColor(index, QColor(*(color.value)))


class BlocksEditor(Editor):
    log = logging.getLogger(__name__)

    def __init__(self, model: ViewerModel):
        super().__init__()

        self.model = model
        self._view = BlocksEditorView()

        blocks = self.model.state.blocks
        blocks.events.added.connect(lambda d: self.block_added(d["item"]))
        blocks.events.deleted.connect(self.block_removed)

        # bindings from view to model
        tab_widget = self._view.tabWidget
        tab_widget.addTabButton.clicked.connect(lambda _: self.add_block())
        tab_widget.tabCloseRequested.connect(self.ask_remove_block)
        tab_widget.tabMoved.connect(lambda ind1, ind2: blocks.swap(ind1, ind2))

        def update_name(index: int) -> None:
            name = tab_widget.tabText(index)
            block: Block = blocks[index]
            block.name = name

        tab_widget.editingFinished.connect(update_name)

        # initialize
        for block in blocks:
            self._add_block_bindings(block)
            self.block_added(block)
        self._view.tabWidget.setCurrentIndex(0)

        self.validate()

    def block_added(self, block: Block):
        samples_editor = SamplesEditor(block.samples)
        devices_editor = DevicesEditor(
            block.devices, self.model.state.payloads, block.samples
        )
        block_diagram_editor = BlockDiagramEditor(block, self.model.state.payloads)

        block_editor = BlockEditorView(
            samplesEditorView=samples_editor._view,
            devicesEditorView=devices_editor._view,
            blockDiagramEditorView=block_diagram_editor._view,
        )

        self._view.tabWidget.addTab(block_editor, block.name)
        self._view.tabWidget.setCurrentWidget(block_editor)

        self.validate()

    def block_removed(self, index: int) -> None:
        self._view.tabWidget.removeTab(index)

        self.validate()

    def add_block(self):
        n_blocks = len(self.model.state.blocks)
        block = Block(name=f"New block {n_blocks + 1}")
        self.model.state.blocks.append(block)
        self._add_block_bindings(block)

    def _add_block_bindings(self, block: Block):
        """
        All changes to the blocks list trigger a call to the validate method.

        If callbacks need to be registered often, refactor into the Block class.
        """
        block.events.name.connect(lambda _: self.validate())

        def add_sample_bindings(sample: Sample):
            sample.events.name.connect(lambda _: self.validate())
            sample.cohorts.events.changed.connect(lambda _: self.validate())

        block.samples.events.added.connect(lambda d: add_sample_bindings(d["item"]))
        block.samples.events.changed.connect(lambda _: self.validate())
        for sample in block.samples:
            add_sample_bindings(sample)

        def add_device_bindings(device: Device):
            device.events.name.connect(lambda _: self.validate())
            device.events.payload_name.connect(lambda _: self.validate())

        block.devices.events.added.connect(lambda d: add_device_bindings(d["item"]))
        block.devices.events.changed.connect(lambda _: self.validate())
        for device in block.devices:
            add_device_bindings(device)

    def ask_remove_block(self, index: int) -> None:
        name = self._view.tabWidget.tabText(index) or f"block {index + 1}"
        response = showYesNoDialog(
            parent=self._view,
            title=f"Delete {name}?",
            text=f"Are you sure you want to delete {name}?",
        )
        if response != QMessageBox.Yes:
            return

        del self.model.state.blocks[index]
        self.log.debug(f"Block {name} deleted")

    def validate(self) -> None:
        invalid_block_indexes = self.model.state.invalid_block_indexes()
        self._view.styleInvalidTabs(invalid_block_indexes)
        self.is_valid = len(invalid_block_indexes) == 0
