import logging
from typing import List, Set

from PySide2.QtCore import Qt, Signal
from PySide2.QtWidgets import (
    QWidget,
    QGridLayout,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QScrollArea,
    QTabWidget,
    QPushButton,
    QTabBar,
    QMessageBox,
)

from .blockdiagram import BlockDiagramEditorView
from ..sample import SampleTableEditorView
from ...editor import Editor
from ...utils import updateStyle, showYesNoDialog
from broadside.components.color import Color
from ....models.block import Block, Sample
from ....models.device import Device
from ...session import Session


class BlockEditorView(QWidget):
    dataChanged = Signal()

    def __init__(self, block: Block, devices: List[Device], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.block = block
        self.devices = devices

        self.setUpUI()
        self.setUpReactivity()

    def setUpUI(self):
        nameLabel = QLabel("Name:")
        nameLineEdit = QLineEdit()
        nameLineEdit.setMinimumWidth(150)
        nameLabel.setBuddy(nameLineEdit)
        self.nameLineEdit = nameLineEdit

        sampleTableEditorView = SampleTableEditorView(self.block)
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

        gridLayout.addWidget(nameLabel, 0, 0, Qt.AlignRight)
        gridLayout.addWidget(nameLineEdit, 0, 1, Qt.AlignLeft)
        gridLayout.setRowStretch(0, 0)

        gridLayout.addWidget(sampleTableEditorView, 1, 0, 1, 2)
        gridLayout.setRowStretch(1, 0)

        # gridLayout.addWidget(blockDiagramEditor, 2, 0, 1, 2)
        # gridLayout.setRowStretch(2, 0)

        gridLayout.addWidget(QWidget(), 2, 0)
        gridLayout.setRowStretch(2, 1)

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

    def setUpReactivity(self):
        def onNameChange():
            name = self.nameLineEdit.text()
            self.block.name = name
            self.dataChanged.emit()

        self.nameLineEdit.textChanged.connect(lambda: onNameChange())
        self.sampleTableEditorView.dataChanged.connect(self.dataChanged.emit)
        self.blockDiagramEditor.dataChanged.connect(self.dataChanged.emit)
        self.sampleTableEditorView.dataChanged.connect(
            self.blockDiagramEditor.dataChangePushed.emit
        )

        # populate fields
        self.nameLineEdit.setText(self.block.name)


class BlockListEditorView(QWidget):
    dataChanged = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setUpUI()
        self.updateDeleteBlockButton()

    def setUpUI(self):
        tabWidget = QTabWidget()
        tabWidget.setMovable(True)

        self.tabWidget = tabWidget

        addBlockButton = QPushButton()
        addBlockButton.setText("Add block")
        self.addBlockButton = addBlockButton

        deleteBlockButton = QPushButton()
        deleteBlockButton.setText("Delete block")
        deleteBlockButton.setObjectName("deleteBlockButton")
        self.deleteBlockButton = deleteBlockButton

        buttonsLayout = QHBoxLayout()
        buttonsLayout.addWidget(addBlockButton)
        buttonsLayout.addWidget(deleteBlockButton)

        layout = QVBoxLayout()
        layout.addWidget(tabWidget)
        layout.addLayout(buttonsLayout)
        self.setLayout(layout)

    def updateDeleteBlockButton(self):
        self.deleteBlockButton.setEnabled(self.tabWidget.count() >= 2)

    def addBlock(self, block: Block, devices: List[Device]) -> None:
        blockEditor = BlockEditorView(block, devices)
        blockEditor.dataChanged.connect(lambda: self.dataChanged.emit())
        self.tabWidget.addTab(blockEditor, block.name)

        def updateTabText(w: BlockEditorView) -> None:
            index = self.tabWidget.indexOf(w)
            self.tabWidget.setTabText(index, w.nameLineEdit.text())

        blockEditor.nameLineEdit.textChanged.connect(lambda: updateTabText(blockEditor))
        updateTabText(blockEditor)
        self.tabWidget.setCurrentWidget(blockEditor)
        self.updateDeleteBlockButton()

    def deleteBlock(self, index: int) -> None:
        self.tabWidget.removeTab(index)
        self.updateDeleteBlockButton()

    def updateDeviceNames(self, names: List[str]) -> None:
        nTabs = self.tabWidget.count()
        for i in range(nTabs):
            editor: BlockEditorView = self.tabWidget.widget(i)
            editor.sampleTableEditorView.deviceNamesModel.updateNames(names)

            samples: List[Sample] = editor.sampleTableEditorView.model.samples
            for sample in samples:
                if sample.deviceName not in names:
                    sample.deviceName = names[0]

    def styleInvalidTabs(self, indexes: Set[int]) -> None:
        tabBar: QTabBar = self.tabWidget.tabBar()
        for index in range(tabBar.count()):
            editor: BlockEditorView = self.tabWidget.widget(index)
            nameLineEdit = editor.nameLineEdit

            if index in indexes:
                tabBar.setTabTextColor(index, Color.Red.qc())
                nameLineEdit.setProperty("valid", "false")
            else:
                tabBar.setTabTextColor(index, Color.Black.qc())
                nameLineEdit.setProperty("valid", "true")

            updateStyle(nameLineEdit)

    def refresh(self):
        for index in range(self.tabWidget.count()):
            blockEditor: BlockEditorView = self.tabWidget.widget(index)
            blockEditor.blockDiagramEditor.dataChangePushed.emit()


class BlockListEditor(Editor):
    log = logging.getLogger(__name__)

    dataChangedFromModel = Signal()  # don't like the name

    def __init__(self, model: Session, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.model = model

        # set up view reactivity
        self.view = BlockListEditorView()
        self.view.addBlockButton.clicked.connect(lambda: self.addBlock())
        self.view.deleteBlockButton.clicked.connect(lambda: self.deleteCurrentBlock())
        self.view.dataChanged.connect(lambda: self.dataChangedFromModel.emit())

        # initialize view
        for block in self.model.blocks:
            self.view.addBlock(block, self.model.devices)
        self.view.tabWidget.setCurrentIndex(0)

        tabBar: QTabBar = self.view.tabWidget.tabBar()
        tabBar.tabMoved.connect(lambda to_, from_: self.moveBlock(to_, from_))
        self.tabBar = tabBar

        # set up remaining reactivity
        self.dataChanged.connect(lambda: self.validate())

        # initialize
        self.validate()

    def addBlock(self):
        count = self.view.tabWidget.count() + 1
        block = Block.from_dict({"name": f"New block {count}"})
        self.model.blocks.append(block)
        self.view.addBlock(block, self.model.devices)

        self.dataChanged.emit()
        self.log.info("New block added")

    def deleteCurrentBlock(self):
        index = self.view.tabWidget.currentIndex()
        name = self.view.tabWidget.tabText(index) or "the current block"

        response = showYesNoDialog(
            parent=self.view,
            title=f"Delete {name}?",
            text=f"Are you sure you want to delete {name}?",
        )
        if response == QMessageBox.Yes:
            del self.model.blocks[index]
            self.view.deleteBlock(index)

            self.dataChanged.emit()
            self.log.info("Block deleted")

    def moveBlock(self, to_: int, from_: int) -> None:
        (self.model.blocks[to_], self.model.blocks[from_]) = (
            self.model.blocks[from_],
            self.model.blocks[to_],
        )

        self.dataChanged.emit()
        self.log.info(f"Block moved to {to_} from {from_}")

    def validate(self):
        invalidTabs: Set[int] = set()

        isBlockNamesValid = True
        for i, block in enumerate(self.model.blocks):
            name = block.name
            if (name == "") or (name is None):
                isBlockNamesValid = False
                invalidTabs.add(i)

        isSampleNamesValid = True
        for i, block in enumerate(self.model.blocks):
            names = [g.name for g in block.samples]
            namesAsSet = set(names)
            if len(names) != len(namesAsSet):
                isSampleNamesValid = False
                invalidTabs.add(i)

        names = [s.name for s in self.model.blocks]
        namesAsSet = set(names)
        isBlockNamesUnique = len(names) == len(namesAsSet)

        for name in namesAsSet:
            indexes = [i for i, _name in enumerate(names) if _name == name]
            if len(indexes) > 1:
                invalidTabs.update(indexes)
        self.view.styleInvalidTabs(invalidTabs)

        self.isValid = isBlockNamesUnique and isBlockNamesValid and isSampleNamesValid
