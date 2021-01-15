import logging

from PySide2.QtCore import Qt
from PySide2.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
    QPushButton,
    QGridLayout,
    QGroupBox,
    QVBoxLayout,
    QPlainTextEdit,
    QTabWidget,
    QLayoutItem,
)

from ..utils import QElidedLabel


class ProjectView(QWidget):
    log = logging.getLogger(__name__)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        statusWidget = self.initStatusWidget()

        noProjectSetLabel = QLabel()
        noProjectSetLabel.setObjectName("noProjectSetLabel")
        noProjectSetLabel.setText("No project set")
        noProjectSetLabel.setAlignment(Qt.AlignCenter)

        layout = QHBoxLayout()
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(statusWidget, stretch=0)
        layout.addSpacing(3)
        layout.addWidget(noProjectSetLabel, stretch=1)

        self.setLayout(layout)

    def initStatusWidget(self) -> QWidget:
        selectProjectButton = QPushButton()
        selectProjectButton.setCursor(Qt.PointingHandCursor)
        selectProjectButton.setObjectName("selectProjectButton")
        selectProjectButton.setText("Select project")
        self.selectProjectButton = selectProjectButton

        pathLabel = QLabel()
        pathLabel.setText("Path:")
        pathLabel.setToolTip("Project path")
        pathLabel.setWordWrap(False)
        pathLabel.setAlignment(Qt.AlignRight)

        pathValueLabel = QElidedLabel()
        pathValueLabel.setText("none")
        pathValueLabel.setToolTip("none")
        pathValueLabel.setWordWrap(False)
        # pathValueLabel.setAlignment(Qt.AlignLeft)
        self.pathValueLabel = pathValueLabel

        nameLabel = QLabel()
        nameLabel.setText("Name:")
        nameLabel.setToolTip("Project name")
        nameLabel.setWordWrap(False)
        nameLabel.setAlignment(Qt.AlignRight)

        nameValueLabel = QElidedLabel()
        nameValueLabel.setText("none")
        nameValueLabel.setToolTip("none")
        nameValueLabel.setWordWrap(False)
        # nameValueLabel.setAlignment(Qt.AlignLeft)
        self.nameValueLabel = nameValueLabel

        projectStatusGrid = QGridLayout()
        projectStatusGrid.setContentsMargins(2, 2, 2, 2)
        projectStatusGrid.setColumnStretch(0, 0)
        projectStatusGrid.setColumnStretch(1, 1)
        projectStatusGrid.addWidget(pathLabel, 0, 0)
        projectStatusGrid.addWidget(nameLabel, 1, 0)
        projectStatusGrid.addWidget(pathValueLabel, 0, 1)
        projectStatusGrid.addWidget(nameValueLabel, 1, 1)

        projectGroupBox = QGroupBox()
        projectGroupBox.setTitle("Current project")
        projectGroupBox.setLayout(projectStatusGrid)

        layout = QVBoxLayout()
        layout.addWidget(selectProjectButton, stretch=0)
        layout.addSpacing(10)
        layout.addWidget(projectGroupBox, stretch=0)
        layout.addStretch(1)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        parentWidget = QWidget()
        parentWidget.setLayout(layout)
        parentWidget.setContentsMargins(0, 0, 0, 0)
        parentWidget.setFixedWidth(250)
        return parentWidget

    def updateView(
        self,
        *,
        deviceListView: QWidget,
        blockListView: QWidget,
        panelListView: QWidget,
        imageListView: QWidget
    ) -> None:
        descriptionTextEdit = QPlainTextEdit()
        self.descriptionTextEdit = descriptionTextEdit

        descriptionLayout = QVBoxLayout()
        descriptionLayout.addWidget(descriptionTextEdit)

        descriptionBox = QGroupBox()
        descriptionBox.setTitle("Description")
        descriptionBox.setLayout(descriptionLayout)
        descriptionBox.setMaximumHeight(130)

        tabWidget = QTabWidget()
        tabWidget.setObjectName("settingsWidget")
        tabWidget.setTabPosition(QTabWidget.North)
        tabWidget.addTab(deviceListView, "Devices")
        tabWidget.addTab(blockListView, "Blocks")
        tabWidget.addTab(panelListView, "Panels")
        tabWidget.addTab(imageListView, "Images")
        self.tabWidget = tabWidget

        settingsLayout = QVBoxLayout()
        settingsLayout.addWidget(descriptionBox, stretch=0)
        settingsLayout.addWidget(tabWidget, stretch=1)

        # replace noProjectSelected label with the settings layout
        layout: QHBoxLayout = self.layout()
        item: QLayoutItem = layout.takeAt(2)  # after statusWidget and spacer
        if item.widget() is not None:
            item.widget().deleteLater()
        layout.addLayout(settingsLayout, stretch=1)

    def setProjectLabels(self, *, path: str, name: str) -> None:
        self.pathValueLabel.setText(path)
        self.pathValueLabel.setToolTip(path)

        self.nameValueLabel.setText(name)
        self.nameValueLabel.setToolTip(name)
