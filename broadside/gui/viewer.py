import logging
from typing import List, Type

from PySide2.QtCore import Qt
from PySide2.QtGui import QCloseEvent
from PySide2.QtWidgets import QWidget, QApplication, QMessageBox

from .components import (
    AnalysisPanel,
    AnnotationPanel,
    BasePanel,
    ProjectPanel,
    MainWindow,
)
from .components.navigation.model import NavigationModel
from .models.project import ProjectModel


class Viewer:
    log = logging.getLogger(__name__)

    def __init__(self, app: QApplication):
        self.app = app

        self.panels: List[Type[BasePanel]] = [
            ProjectPanel,
            AnnotationPanel,
            AnalysisPanel,
        ]

        panelNames = [p.name for p in self.panels]

        self.window = MainWindow()
        self.window.initCentralWidget(panelNames=panelNames)

        self.initModel()
        self.initNav()
        self.initWindowReactivity()

    def initModel(self):
        self.model = ProjectModel()

        def updateTitle():
            name = self.model.name
            isStale = self.model.isStale

            title = (
                "Broadside" + (f" – {name}" if name else "") + ("*" if isStale else "")
            )
            self.window.setWindowTitle(title)

        self.model.isStaleChanged.connect(lambda: updateTitle())
        self.model.projectChanged.connect(lambda: updateTitle())

    def initNav(self):
        self.navModel = NavigationModel(n=len(self.panels))

        # set up reactivity
        self.navModel.indexChanged.connect(lambda: self.refresh())
        self.window.navPanel.backButton.clicked.connect(
            lambda: self.navModel.move_back()
        )
        self.window.navPanel.nextButton.clicked.connect(
            lambda: self.navModel.move_next()
        )

        # initial state
        self.refresh()

    def refresh(self):
        # delete current widget ...
        widget: QWidget = self.window.panelContainer.itemAt(0).widget()
        widget.deleteLater()

        # ... and add the next one
        index = self.navModel.index
        panel = self.panels[index](model=self.model, parent=self.window)
        self.window.panelContainer.addWidget(panel.view)

        # refresh navigation panel
        self.window.navPanel.setState(self.navModel.index, False)
        self.window.navPanel.backButton.setEnabled(not self.navModel.first)
        self.window.navPanel.nextButton.setEnabled(not self.navModel.last)

    def initWindowReactivity(self):
        self.window.saveAction.triggered.connect(lambda: self.model.save())

        def aboutToQuit(event: QCloseEvent = None):
            if self.model.path is None:
                self.log.info("No project set; quitting")
                event.accept()
                return

            name = self.model.name

            if not self.model.isStale:
                self.log.info(f"Project {name} already saved; quitting")
                event.accept()
                return

            msgBox = QMessageBox()
            msgBox.setWindowTitle("About to quit")
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
                self.model.save()
                self.log.info(f"Project {name} saved; quitting")
                event.accept()
            elif response == QMessageBox.Discard:
                self.log.info(f"Project {name} not saved; quitting")
                event.accept()
            elif response == QMessageBox.Cancel:
                self.log.info(f"Project {name} not saved; not quitting")
                event.ignore()

        self.window.aboutToClose.connect(lambda event: aboutToQuit(event))
        self.window.quitAction.triggered.connect(lambda: self.window.close())

    def show(self):
        self.window.show()
