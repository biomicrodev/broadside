from typing import List

from PySide2.QtCore import Qt
from PySide2.QtWidgets import (
    QWidget,
    QPushButton,
    QTabWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QGridLayout,
)

from broadside.gui.models.samplegroup import SampleGroup
from broadside.gui.utils import showDeleteDialog


class SampleGroupWidget(QWidget):
    def __init__(self, *args, _init_name: str = "", **kwargs):
        super().__init__(*args, **kwargs)

        self._init_name = _init_name

        self.setUpUI()

    def setUpUI(self):
        nameLabel = QLabel("Name:")
        nameLabelEdit = QLineEdit(self._init_name)
        nameLabel.setBuddy(nameLabelEdit)
        self.nameLabelEdit = nameLabelEdit

        layout = QGridLayout()
        layout.setcolumnStretch(0, 0)
        layout.setcolumnStretch(1, 1)
        layout.setColumnMinimumWidth(0, 200)
        layout.setColumnMinimumWidth(1, 200)

        layout.addWidget(nameLabel, 0, 0, Qt.AlignRight)
        layout.addWidget(nameLabelEdit, 0, 1, Qt.AlignLeft)
        layout.setRowStretch(0, 1)

        layout.addWidget(QWidget(), 2, 0)
        layout.setRowStretch(1, 1)

        self.setLayout(layout)


class SampleGroupListWidget(QWidget):
    def __init__(self, *args, sampleGroups: List[SampleGroup] = None, **kwargs):
        super().__init__(*args, **kwargs)

        self._sampleGroups = sampleGroups or []

        self.setUpUI()

    def setUpUI(self):
        sampleGroupTabWidget = QTabWidget()
        self.tabWidget = sampleGroupTabWidget

        addSampleGroupButton = QPushButton()
        addSampleGroupButton.setText("Add sample group")
        self.addSampleGroupButton = addSampleGroupButton

        deleteSampleGroupButton = QPushButton()
        deleteSampleGroupButton.setText("Delete sample group")
        deleteSampleGroupButton.setObjectName("DeleteSampleButton")
        self.deleteSampleGroupButton = deleteSampleGroupButton
        self._updateDeleteButton()

        buttonsLayout = QHBoxLayout()
        buttonsLayout.addStretch(1)
        buttonsLayout.addWidget(addSampleGroupButton)
        buttonsLayout.addWidget(deleteSampleGroupButton)

        layout = QVBoxLayout()
        layout.addWidget(sampleGroupTabWidget)
        layout.addLayout(buttonsLayout)
        self.setLayout(layout)

    def _updateDeleteButton(self):
        self.deleteSampleGroupButton.setEnabled(self.tabWidget.count() >= 2)

    def setUpReactivity(self):
        def addNewSampleGroup():
            nWidgets = self.tabWidget.count()
            name = f"New sample group {str(nWidgets + 1)}"

            widget = SampleGroupWidget(_init_name=name)
            self.tabWidget.addTab(widget, name)

            def updateTabText(name: str) -> None:
                index = self.tabWidget.indexOf(widget)
                self.tabWidget.setTabText(index, name)

            widget.nameLabelEdit.textChanged.connect(lambda name: updateTabText(name))

            index = self.tabWidget.indexOf(widget)
            self.tabWidget.setCurrentIndex(index)

            self._updateDeleteButton()

        self.addSampleGroupButton.clicked.connect(lambda: addNewSampleGroup())

        def deleteSampleGroup():
            index = self.tabWidget.currentIndex()
            name = self.tabWidget.tabText(index)

            response = showDeleteDialog(
                title=f"Delete {name}?", text=f"Are you sure you want to delete {name}?"
            )
            if response == QMessageBox.Yes:
                self.tabWidget.removeTab(index)

                self._updateDeleteButton()

        self.deleteSampleGroupButton.clicked.connect(lambda: deleteSampleGroup())
