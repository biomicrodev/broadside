import logging
from typing import List

from PySide2.QtCore import Signal, Qt
from PySide2.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QLineEdit,
    QGridLayout,
    QTabWidget,
    QPushButton,
    QHBoxLayout,
    QTabBar,
    QMessageBox,
    QScrollArea,
)

from .sample import SampleTableEditorView
from ..editor import Editor
from ..utils import showYesNoDialog, updateStyle
from ...color import Color
from ...models.block import Block, Sample


class BlockEditorView(QWidget):
    dataChanged = Signal()

    def __init__(self, block: Block, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.block = block

        self.setUpUI()
        self.setUpReactivity()

    def setUpUI(self):
        nameLabel = QLabel("Name:")
        nameLineEdit = QLineEdit()
        nameLineEdit.setMinimumWidth(150)
        nameLabel.setBuddy(nameLineEdit)
        self.nameLineEdit = nameLineEdit

        sampleTableEditorView = SampleTableEditorView(self.block.samples)
        sampleTableEditorView.setMaximumWidth(600)
        self.sampleTableEditorView = sampleTableEditorView

        layout = QGridLayout()
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 1)

        layout.addWidget(nameLabel, 0, 0, Qt.AlignRight)
        layout.addWidget(nameLineEdit, 0, 1, Qt.AlignLeft)
        layout.setRowStretch(0, 0)

        layout.addWidget(sampleTableEditorView, 1, 0, 1, 2)
        layout.setRowStretch(1, 0)

        layout.addWidget(QWidget(), 2, 0)
        layout.setRowStretch(2, 1)

        parentWidget = QWidget()
        parentWidget.setLayout(layout)
        parentWidget.setMinimumWidth(500)

        scrollArea = QScrollArea()
        scrollArea.setWidget(parentWidget)

        parentLayout = QVBoxLayout()
        parentLayout.addWidget(scrollArea, 1)
        self.setLayout(parentLayout)

    def setUpReactivity(self):
        def onNameChange():
            name = self.nameLineEdit.text()
            self.block.name = name
            self.dataChanged.emit()

        self.nameLineEdit.textChanged.connect(lambda: onNameChange())

        self.sampleTableEditorView.dataChanged.connect(lambda: self.dataChanged.emit())

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

    def addBlock(self, block: Block) -> None:
        blockEditor = BlockEditorView(block)
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


class BlockListEditor(Editor):
    log = logging.getLogger(__name__)

    def __init__(self, blocks: List[Block], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.blocks = blocks

        # set up view reactivity
        self.view = BlockListEditorView()
        self.view.addBlockButton.clicked.connect(lambda: self.addBlock())
        self.view.deleteBlockButton.clicked.connect(lambda: self.deleteCurrentBlock())
        self.view.dataChanged.connect(lambda: self.dataChanged.emit())

        # initialize view
        for block in self.blocks:
            self.view.addBlock(block)
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
        self.blocks.append(block)
        self.view.addBlock(block)

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
            del self.blocks[index]
            self.view.deleteBlock(index)

            self.dataChanged.emit()
            self.log.info("Block deleted")

    def moveBlock(self, to_: int, from_: int) -> None:
        (self.blocks[to_], self.blocks[from_]) = (
            self.blocks[from_],
            self.blocks[to_],
        )

        self.dataChanged.emit()
        self.log.info(f"Block moved to {to_} from {from_}")

    def validate(self):
        # are block names unique?
        names = [s.name for s in self.blocks]
        namesAsSet = set(names)

        # which block names conflict?
        duplicates = set()
        for name in namesAsSet:
            indexes = [i for i, _name in enumerate(names) if _name == name]
            if len(indexes) > 1:
                duplicates.update(indexes)

        for index in range(self.tabBar.count()):
            editor: BlockEditorView = self.view.tabWidget.widget(index)
            nameLineEdit = editor.nameLineEdit

            if index in duplicates:
                self.tabBar.setTabTextColor(index, Color.Red.qc())
                nameLineEdit.setProperty("valid", "false")
            else:
                self.tabBar.setTabTextColor(index, Color.Black.qc())
                nameLineEdit.setProperty("valid", "true")

            updateStyle(nameLineEdit)

        # are sample names for each block unique?
        blockNamesValid = True
        for block in self.blocks:
            names = [g.name for g in block.samples]
            namesAsSet = set(names)
            if len(names) != len(namesAsSet):
                blockNamesValid = False
                break

        self.isValid = (len(namesAsSet) == len(names)) and blockNamesValid
