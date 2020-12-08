import logging
from typing import List

from PySide2.QtCore import QObject, Signal, Qt
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
)

from .sample import SampleTableEditorView
from ..editor import Editor
from ..utils import showYesNoDialog
from ...color import Color
from ...models.samplegroup import SampleGroup


class SampleGroupEditorView(QWidget):
    dataChanged = Signal()

    def __init__(self, sampleGroup: SampleGroup, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.sampleGroup = sampleGroup

        self.setUpUI()
        self.setUpReactivity()

    def setUpUI(self):
        nameLabel = QLabel("Name:")
        nameLineEdit = QLineEdit()
        nameLineEdit.setMinimumWidth(150)
        nameLabel.setBuddy(nameLineEdit)
        self.nameLineEdit = nameLineEdit

        sampleTableEditorView = SampleTableEditorView(
            samples=self.sampleGroup.samples, cohorts=self.sampleGroup.cohorts
        )
        sampleTableEditorView.setMaximumWidth(600)
        self.sampleTableEditorview = sampleTableEditorView

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

        self.setLayout(layout)

    def setUpReactivity(self):
        def onNameChange():
            name = self.nameLineEdit.text()
            self.sampleGroup.name = name
            self.dataChanged.emit()

        self.nameLineEdit.textChanged.connect(lambda: onNameChange())

        # populate fields
        self.nameLineEdit.setText(self.sampleGroup.name)


class SampleGroupListEditorView(QWidget):
    dataChanged = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setUpUI()
        self.updateDeleteSampleGroupButton()

    def setUpUI(self):
        tabWidget = QTabWidget()
        tabWidget.setMovable(True)

        self.tabWidget = tabWidget

        addSampleGroupButton = QPushButton()
        addSampleGroupButton.setText("Add group")
        self.addSampleGroupButton = addSampleGroupButton

        deleteSampleGroupButton = QPushButton()
        deleteSampleGroupButton.setText("Delete group")
        deleteSampleGroupButton.setObjectName("deleteSampleGroupButton")
        self.deleteSampleGroupButton = deleteSampleGroupButton

        buttonsLayout = QHBoxLayout()
        buttonsLayout.addWidget(addSampleGroupButton)
        buttonsLayout.addWidget(deleteSampleGroupButton)

        layout = QVBoxLayout()
        layout.addWidget(tabWidget)
        layout.addLayout(buttonsLayout)
        self.setLayout(layout)

    def updateDeleteSampleGroupButton(self):
        self.deleteSampleGroupButton.setEnabled(self.tabWidget.count() >= 2)

    def addSampleGroup(self, sampleGroup: SampleGroup) -> None:
        sampleGroupEditor = SampleGroupEditorView(sampleGroup)
        sampleGroupEditor.dataChanged.connect(lambda: self.dataChanged.emit())
        self.tabWidget.addTab(sampleGroupEditor, sampleGroup.name)

        index = self.tabWidget.indexOf(sampleGroupEditor)
        sampleGroupEditor.nameLineEdit.textChanged.connect(
            lambda: self.tabWidget.setTabText(
                index, sampleGroupEditor.nameLineEdit.text()
            )
        )
        self.tabWidget.setCurrentIndex(index)

        self.updateDeleteSampleGroupButton()

    def deleteSampleGroup(self, index: int) -> None:
        self.tabWidget.removeTab(index)

        self.updateDeleteSampleGroupButton()


class SampleGroupListEditor(Editor):
    log = logging.getLogger(__name__)

    def __init__(self, sampleGroups: List[SampleGroup], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.sampleGroups = sampleGroups

        # set up view reactivity
        self.view = SampleGroupListEditorView()
        self.view.addSampleGroupButton.clicked.connect(lambda: self.addSampleGroup())
        self.view.deleteSampleGroupButton.clicked.connect(
            lambda: self.deleteCurrentSampleGroup()
        )
        self.view.dataChanged.connect(lambda: self.dataChanged.emit())

        # initialize view
        for group in self.sampleGroups:
            self.view.addSampleGroup(group)
        self.view.tabWidget.setCurrentIndex(0)

        tabBar: QTabBar = self.view.tabWidget.tabBar()
        tabBar.tabMoved.connect(lambda to_, from_: self.moveSampleGroup(to_, from_))
        self.tabBar = tabBar

        # set up remaining reactivity
        self.dataChanged.connect(lambda: self.validate())

        # initialize
        self.validate()

    def addSampleGroup(self):
        count = self.view.tabWidget.count() + 1
        sampleGroup = SampleGroup.from_dict({"name": f"New group {count}"})
        self.sampleGroups.append(sampleGroup)
        self.view.addSampleGroup(sampleGroup)

        self.dataChanged.emit()
        self.log.info("New sample group added")

    def deleteCurrentSampleGroup(self):
        index = self.view.tabWidget.currentIndex()
        name = self.view.tabWidget.tabText(index) or "the current sample group"

        response = showYesNoDialog(
            parent=self.view,
            title=f"Delete {name}?",
            text=f"Are you sure you want to delete {name}?",
        )
        if response == QMessageBox.Yes:
            del self.sampleGroups[index]
            self.view.deleteSampleGroup(index)

            self.dataChanged.emit()
            self.log.info("Sample group deleted")

    def moveSampleGroup(self, to_: int, from_: int) -> None:
        (self.sampleGroups[to_], self.sampleGroups[from_]) = (
            self.sampleGroups[from_],
            self.sampleGroups[to_],
        )

        self.dataChanged.emit()
        self.log.info(f"Sample group moved to {to_} from {from_}")

    def validate(self):
        names = [s.name for s in self.sampleGroups]
        namesAsSet = set(names)

        self.isValid = len(namesAsSet) == len(names)

        duplicates = set()
        for name in namesAsSet:
            indexes = [i for i, _name in enumerate(names) if _name == name]
            if len(indexes) > 1:
                duplicates.update(indexes)

        for index in range(self.tabBar.count()):
            if index in duplicates:
                self.tabBar.setTabTextColor(index, Color.Red.qc())
            else:
                self.tabBar.setTabTextColor(index, Color.Black.qc())
