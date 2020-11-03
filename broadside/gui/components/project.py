from PySide2.QtCore import Qt
from PySide2.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QGridLayout,
    QLabel,
    QSpacerItem,
    QSizePolicy,
    QGroupBox,
    QTabWidget,
    QTabBar,
    QLayout,
)

from broadside.gui.components.devices import DevicesWidget


class ProjectWidget(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent=parent)

        leftPanel = self.createProjectStatusLayout()
        settingsWidget = self.createProjectSettingsLayout()

        layout = QHBoxLayout()
        layout.setContentsMargins(9, 9, 9, 9)
        layout.addLayout(leftPanel, stretch=0)
        layout.addSpacing(3)
        layout.addWidget(settingsWidget, stretch=1)

        self.setLayout(layout)

    def createProjectStatusLayout(self) -> QLayout:
        selectProjectButton = QPushButton()
        selectProjectButton.setObjectName("selectProjectButton")
        selectProjectButton.setText("Select project")

        pathLabel = QLabel()
        pathLabel.setText("Path:")
        pathLabel.setToolTip("Project path")
        pathLabel.setWordWrap(False)
        pathLabel.setAlignment(Qt.AlignRight)

        pathValueLabel = QLabel()
        pathValueLabel.setText("none")
        pathValueLabel.setToolTip("none")
        pathValueLabel.setWordWrap(False)

        nameLabel = QLabel()
        nameLabel.setText("Name:")
        nameLabel.setToolTip("Project name")
        nameLabel.setWordWrap(False)
        nameLabel.setAlignment(Qt.AlignRight)

        nameValueLabel = QLabel()
        nameValueLabel.setText("none")
        nameValueLabel.setToolTip("none")
        nameValueLabel.setWordWrap(False)

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
        layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )

        self.pathValueLabel = pathValueLabel
        self.nameValueLabel = nameValueLabel

        return layout

    def createProjectSettingsLayout(self) -> QWidget:
        blocksLabel = QLabel()
        blocksLabel.setText("blocks")

        blocksLayout = QVBoxLayout()
        blocksLayout.addWidget(blocksLabel)

        blocksWidget = QWidget()
        blocksWidget.setLayout(blocksLayout)

        panelsWidget = QWidget()
        # panelsWidget.setLayout()

        imageGroupsWidget = QWidget()
        # imageGroupsWidget.setLayout()

        devicesWidget = DevicesWidget()

        settingsWidget = QTabWidget()
        settingsWidget.setObjectName("settingsWidget")
        settingsWidget.setTabPosition(QTabWidget.North)
        settingsWidget.addTab(blocksWidget, "Blocks")
        settingsWidget.addTab(panelsWidget, "Panels")
        settingsWidget.addTab(imageGroupsWidget, "Image Groups")
        settingsWidget.addTab(devicesWidget, "Devices")

        settingsTabBar: QTabBar = settingsWidget.tabBar()
        settingsTabBar.setObjectName("settingsTabBar")

        return settingsWidget
