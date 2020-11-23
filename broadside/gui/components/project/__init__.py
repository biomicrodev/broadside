import logging
from pathlib import Path

from PySide2.QtCore import Qt, Signal, QDir
from PySide2.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QPushButton,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QFileDialog,
    QTabWidget,
    QMessageBox,
    QPlainTextEdit,
)

from .device import DeviceListView
from ..panel import BasePanel
from ...models.project import ProjectModel, SaveAction
from ...utils import QElidedLabel


class ProjectWidget(QWidget):
    log = logging.getLogger(__name__)

    projectSelected = Signal(Path)

    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)

        self.initUI()
        self.initReactivity()

    def initUI(self):
        statusWidget = self.initStatusWidget()
        settingsLayout = self.initSettingsLayout()

        layout = QHBoxLayout()
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(statusWidget, stretch=0)
        layout.addSpacing(3)
        layout.addWidget(settingsLayout, stretch=1)

        self.setLayout(layout)

    def initStatusWidget(self) -> QWidget:
        selectProjectButton = QPushButton()
        selectProjectButton.setObjectName("SelectProjectButton")
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
        parentWidget.setFixedWidth(200)
        return parentWidget

    def initSettingsLayout(self) -> QWidget:
        settingsWidget = QLabel()
        settingsWidget.setText("No project selected")
        settingsWidget.setStyleSheet("font-size: 48px; color: hsl(0, 0%, 80%);")
        settingsWidget.setAlignment(Qt.AlignCenter)
        return settingsWidget

    def initReactivity(self):
        self.selectProjectButton.clicked.connect(lambda: self.selectProject())

    def selectProject(self) -> None:
        dialog = QFileDialog(self, Qt.Dialog)
        dialog.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog)
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setLabelText(QFileDialog.LookIn, "Select project folder")
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        dialog.setViewMode(QFileDialog.Detail)
        dialog.setDirectory(QDir.homePath())

        if dialog.exec_():
            paths = dialog.selectedFiles()
            assert len(paths) == 1
            path = Path(paths[0])
            self.log.info(f"{path} picked")
            self.projectSelected.emit(path)

    def updateState(self, *, path: Path, name: str, description: str) -> None:
        self.pathValueLabel.setText(str(path.parent))
        self.pathValueLabel.setToolTip(str(path.parent))

        self.nameValueLabel.setText(name)
        self.nameValueLabel.setToolTip(name)

        # TODO: could use refactoring later on to not have to recreate the widget every time
        descriptionTextEdit = QPlainTextEdit()
        descriptionTextEdit.setPlainText(description)
        self.descriptionTextEdit = descriptionTextEdit

        descriptionLayout = QVBoxLayout()
        descriptionLayout.addWidget(descriptionTextEdit)

        descriptionBox = QGroupBox()
        descriptionBox.setTitle("Description")
        descriptionBox.setLayout(descriptionLayout)
        descriptionBox.setMaximumHeight(130)

        deviceListWidget = DeviceListView()
        blockListWidget = QWidget()
        imageListWidget = QWidget()

        settingsTabWidget = QTabWidget()
        settingsTabWidget.setObjectName("SettingsWidget")
        settingsTabWidget.setTabPosition(QTabWidget.North)
        settingsTabWidget.addTab(deviceListWidget, "Devices")
        settingsTabWidget.addTab(blockListWidget, "Blocks")
        settingsTabWidget.addTab(imageListWidget, "Images")

        settingsLayout = QVBoxLayout()
        settingsLayout.addWidget(descriptionBox, stretch=0)
        settingsLayout.addWidget(settingsTabWidget, stretch=1)

        # replace no-project-selected widget with the settings widget
        layout: QHBoxLayout = self.layout()
        widget: QWidget = layout.itemAt(2).widget()
        widget.deleteLater()

        layout.addLayout(settingsLayout, stretch=1)


class ProjectPanel(BasePanel):
    log = logging.getLogger(__name__)

    name = "Project"

    def __init__(self, model: ProjectModel, parent: QWidget = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.model = model
        self.view = ProjectWidget(parent=parent)

        self.setUpReactivity()

    def setUpReactivity(self):
        def askSave(newPath: Path):
            name = self.model.name

            msgBox = QMessageBox()
            msgBox.setWindowTitle("Unsaved changes")
            msgBox.setIcon(QMessageBox.Question)
            msgBox.setWindowModality(Qt.ApplicationModal)
            msgBox.setText(
                f"You have unsaved changes pending for project {name}.\n"
                "Do you want to save your changes?"
            )
            msgBox.setStandardButtons(
                QMessageBox.Save | QMessageBox.Cancel | QMessageBox.Discard
            )
            msgBox.setDefaultButton(QMessageBox.Cancel)

            response = msgBox.exec_()
            if response == QMessageBox.Save:
                action = SaveAction.Save
            elif response == QMessageBox.Discard:
                action = SaveAction.Discard
            elif response == QMessageBox.Cancel:
                action = SaveAction.Cancel
            else:
                raise RuntimeError(f"Unknown response {response}")

            self.log.info(f"Save asked; user responded with {action}")

            self.model.onSaveResponse(newPath=newPath, action=action)

        # model to view
        self.model.askSave.connect(lambda newPath: askSave(newPath))

        def updateState():
            self.view.updateState(
                path=self.model.path,
                name=self.model.name,
                description=self.model.description,
            )

            self.view.descriptionTextEdit.textChanged.connect(
                lambda: setattr(
                    self.model,
                    "description",
                    self.view.descriptionTextEdit.toPlainText(),
                )
            )

        self.model.projectChanged.connect(lambda: updateState())

        # view to model
        self.view.projectSelected.connect(
            lambda path: setattr(self.model, "path", path)
        )
