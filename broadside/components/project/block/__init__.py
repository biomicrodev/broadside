import logging
from typing import List, Set

from PySide2.QtCore import Signal
from PySide2.QtWidgets import (
    QWidget,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QTabBar,
    QMessageBox,
)

from .blockdiagram import BlockDiagramEditorView
from .sample import SampleTableEditorView
from ...color import Color
from ...editor import Editor
from ...utils import showYesNoDialog, EditableTabWidget
from ...viewermodel import ViewerModel
from ....models.block import Block
from ....models.device import Device


class BlockEditorView(QWidget):
    blockChanged = Signal()

    def __init__(self, block: Block, devices: List[Device], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.block = block
        self.devices = devices

        self.initUI()
        self.initBindings()

    def initUI(self):
        sampleTableEditorView = SampleTableEditorView(self.block, self.devices)
        sampleTableEditorView.setMinimumWidth(500)
        sampleTableEditorView.setMinimumHeight(500)
        self.sampleTableEditorView = sampleTableEditorView

        blockDiagramEditor = BlockDiagramEditorView(
            block=self.block, devices=self.devices
        )
        blockDiagramEditor.setMinimumWidth(800)
        blockDiagramEditor.setMinimumHeight(400)
        self.blockDiagramEditor = blockDiagramEditor

        gridLayout = QGridLayout()
        gridLayout.setColumnStretch(0, 0)
        gridLayout.setColumnStretch(1, 1)
        gridLayout.setVerticalSpacing(20)

        gridLayout.addWidget(sampleTableEditorView, 0, 0, 1, 2)
        gridLayout.setRowStretch(0, 0)

        gridLayout.addWidget(QWidget(), 1, 0)
        gridLayout.setRowStretch(1, 1)

        layout = QHBoxLayout()
        layout.addLayout(gridLayout, 0)
        layout.addSpacing(30)
        layout.addWidget(blockDiagramEditor, 0)

        parentWidget = QWidget()
        parentWidget.setLayout(layout)

        scrollArea = QScrollArea()
        scrollArea.setWidget(parentWidget)
        scrollArea.setWidgetResizable(False)

        parentLayout = QVBoxLayout()
        parentLayout.addWidget(scrollArea, 1)
        self.setLayout(parentLayout)

    def initBindings(self):
        self.blockDiagramEditor.blockChanged.connect(lambda: self.blockChanged.emit())
        self.sampleTableEditorView.samplesChanged.connect(
            lambda: self.blockChanged.emit()
        )
        self.sampleTableEditorView.samplesChanged.connect(
            lambda: self.blockDiagramEditor.refresh()
        )

    def refresh(self):
        self.sampleTableEditorView.refresh()
        self.blockDiagramEditor.refresh()


class BlockListEditorView(QWidget):
    blockListChanged = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.initUI()
        self.updateTabsClosable()

    def initUI(self):
        self.tabWidget = EditableTabWidget(addButtonText="Add new block")

        layout = QVBoxLayout()
        layout.addWidget(self.tabWidget)
        self.setLayout(layout)

    def updateTabsClosable(self):
        self.tabWidget.setTabsClosable(self.tabWidget.count() >= 2)

    def addBlock(self, block: Block, devices: List[Device]) -> None:
        blockEditor = BlockEditorView(block, devices)
        blockEditor.blockChanged.connect(lambda: self.blockListChanged.emit())
        self.tabWidget.addTab(blockEditor, block.name)
        self.tabWidget.setCurrentWidget(blockEditor)
        self.updateTabsClosable()

    def deleteBlock(self, index: int) -> None:
        self.tabWidget.removeTab(index)
        self.updateTabsClosable()

    # def updateDeviceNames(self, names: List[str]) -> None:
    #     nTabs = self.tabWidget.count()
    #     for i in range(nTabs):
    #         editor: BlockEditorView = self.tabWidget.widget(i)
    #         editor.sampleTableEditorView.deviceNamesModel.updateNames(names)
    #
    #         samples: List[Sample] = editor.sampleTableEditorView.model.samples
    #         for sample in samples:
    #             if sample.device_name not in names:
    #                 sample.device_name = names[0]

    def styleInvalidTabs(self, indexes: Set[int]) -> None:
        tabBar: QTabBar = self.tabWidget.tabBar()
        for index in range(tabBar.count()):
            tabBar.setTabTextColor(
                index, Color.Red.qc() if index in indexes else Color.Black.qc()
            )

    def refresh(self):
        for index in range(self.tabWidget.count()):
            blockEditor: BlockEditorView = self.tabWidget.widget(index)
            blockEditor.refresh()


class BlockListEditor(Editor):
    log = logging.getLogger(__name__)

    blockListChanged = Signal()

    def __init__(self, model: ViewerModel, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.model = model
        self.blocks = model.blocks  # for convenience, mostly
        self.view = BlockListEditorView()

        # set up bindings
        self.view.blockListChanged.connect(lambda: self.blockListChanged.emit())
        self.blockListChanged.connect(lambda: self.validate())

        tabWidget = self.view.tabWidget
        tabWidget.addTabButton.clicked.connect(lambda: self.addBlock())
        tabWidget.tabCloseRequested.connect(lambda index: self.deleteBlock(index))
        tabWidget.tabMoved.connect(lambda to_, from_: self.moveBlock(to_, from_))

        def updateName(index: int) -> None:
            name = tabWidget.tabText(index)
            if self.blocks[index].name != name:
                self.blocks[index].name = name
                self.blockListChanged.emit()

        tabWidget.editingFinished.connect(lambda index: updateName(index))

        # initialize
        for block in self.blocks:
            self.view.addBlock(block, self.model.devices)
        self.view.tabWidget.setCurrentIndex(0)

        self.validate()

    def addBlock(self):
        count = self.view.tabWidget.count() + 1
        block = Block.from_dict({"name": f"New block {count}"})
        self.blocks.append(block)
        self.view.addBlock(block, self.model.devices)

        self.blockListChanged.emit()
        self.log.info("New block added")

    def deleteBlock(self, index: int) -> None:
        name = self.view.tabWidget.tabText(index) or "the current block"

        response = showYesNoDialog(
            parent=self.view,
            title=f"Delete {name}?",
            text=f"Are you sure you want to delete {name}?",
        )
        if response == QMessageBox.Yes:
            del self.blocks[index]
            self.view.deleteBlock(index)

            self.blockListChanged.emit()
            self.log.info("Block deleted")

    def moveBlock(self, to_: int, from_: int) -> None:
        (self.blocks[to_], self.blocks[from_]) = (self.blocks[from_], self.blocks[to_])

        self.blockListChanged.emit()
        self.log.info(f"Block moved to {to_} from {from_}")

    def validate(self):
        invalidBlockIndexes = self.model.state.invalid_block_indexes()
        self.view.styleInvalidTabs(invalidBlockIndexes)
        self.isValid = len(invalidBlockIndexes) == 0
