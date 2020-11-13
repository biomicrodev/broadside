from pathlib import Path
from typing import List, Type

from PySide2.QtWidgets import QApplication, QWidget, QVBoxLayout, QFrame

from broadside.gui.components import (
    AnalysisPanel,
    AnnotationPanel,
    BasePanel,
    ProjectPanel,
    MainWindow,
)
from broadside.gui.components.navigation.model import NavigationModel
from broadside.gui.components.navigation.view import NavigationWidget

styles_dir = Path(__file__).parent.resolve() / "styles"


class Viewer:
    def __init__(self, *, app: QApplication):
        self.window = MainWindow()

        self.panels: List[Type[BasePanel]] = [
            ProjectPanel,
            AnnotationPanel,
            AnalysisPanel,
        ]

        self.initUI()
        self.initNav()

    def initUI(self):
        panelNames: List[str] = [panel.name for panel in self.panels]
        self.navPanel = NavigationWidget(labels=panelNames)

        panelContainer = QVBoxLayout()
        panelContainer.setSpacing(0)
        panelContainer.setContentsMargins(0, 0, 0, 0)
        panelContainer.addWidget(QWidget())
        self.panelContainer = panelContainer

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Plain)
        line.setStyleSheet("color: lightgray")

        centralLayout = QVBoxLayout()
        centralLayout.setContentsMargins(0, 0, 0, 0)
        centralLayout.setSpacing(0)
        centralLayout.addWidget(self.navPanel, stretch=0)
        centralLayout.addWidget(line, stretch=0)
        centralLayout.addLayout(self.panelContainer, stretch=1)

        widget = QWidget()
        widget.setLayout(centralLayout)
        self.window.setCentralWidget(widget)

    def initNav(self):
        self.navModel = NavigationModel(n=len(self.panels))

        # set up reactivity
        self.navModel.indexChanged.connect(lambda: self.refresh())
        self.navPanel.backButton.clicked.connect(lambda: self.navModel.move_back())
        self.navPanel.nextButton.clicked.connect(lambda: self.navModel.move_next())

        # initial state
        self.refresh()

    def refresh(self):
        item: QWidget = self.panelContainer.itemAt(0).widget()
        item.deleteLater()

        index = self.navModel.index
        panel = self.panels[index]()
        self.panelContainer.addWidget(panel.view)

        # refresh navigation panel
        self.navPanel.setState(self.navModel.index, False)
        self.navPanel.backButton.setEnabled(not self.navModel.first)
        self.navPanel.nextButton.setEnabled(not self.navModel.last)

    def setStyleSheet(self, style: str = "default") -> None:
        filepath = styles_dir / f"{style}.qss"

        if not filepath.is_file():
            filepath = styles_dir / "default.qss"

        with open(str(filepath), "r") as file:
            self.window.setStyleSheet(file.read())

    def show(self):
        self.window.show()
