import logging

from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
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

from ...utils import QElidedLabel


class ProjectView(QWidget):
    log = logging.getLogger(__name__)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

        statusLayout = QVBoxLayout()
        statusLayout.addWidget(selectProjectButton, stretch=0)
        statusLayout.addSpacing(10)
        statusLayout.addWidget(projectGroupBox, stretch=0)
        statusLayout.addStretch(1)
        statusLayout.setContentsMargins(0, 0, 0, 0)
        statusLayout.setSpacing(0)

        statusWidget = QWidget()
        statusWidget.setLayout(statusLayout)
        statusWidget.setContentsMargins(0, 0, 0, 0)
        statusWidget.setFixedWidth(250)

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

    def updateEditors(
        self,
        *,
        payloadsView: QWidget,
        blocksView: QWidget,
        # panelsView: QWidget,
        # imagesView: QWidget
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
        tabWidget.addTab(payloadsView, "Payloads")
        tabWidget.addTab(blocksView, "Blocks")
        # tabWidget.addTab(panelsView, "Panels")
        # tabWidget.addTab(imagesView, "Images")
        self.tabWidget = tabWidget

        layout = QVBoxLayout()
        layout.addWidget(descriptionBox, stretch=0)
        layout.addWidget(tabWidget, stretch=1)

        # replace no_project_selected_label with the settings layout
        parentLayout: QHBoxLayout = self.layout()
        item: QLayoutItem = parentLayout.takeAt(2)  # after statusWidget and spacer
        if item.widget() is not None:
            item.widget().deleteLater()
        parentLayout.addLayout(layout, stretch=1)

    def setProjectLabels(self, *, path: str, name: str) -> None:
        self.pathValueLabel.setText(path)
        self.pathValueLabel.setToolTip(path)

        self.nameValueLabel.setText(name)
        self.nameValueLabel.setToolTip(name)
