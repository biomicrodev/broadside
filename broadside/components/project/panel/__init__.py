import logging
from typing import Set

from qtpy.QtCore import Signal
from qtpy.QtWidgets import QWidget, QVBoxLayout, QTabBar, QMessageBox, QScrollArea

from .channel import ChannelTableEditorView
from ...color import Color
from ...editor import Editor
from ...utils import EditableTabWidget, showYesNoDialog
from ...viewermodel import ViewerModel
from ....models.panel import Panel


class PanelEditorView(QWidget):
    panelChanged = Signal()

    def __init__(self, panel: Panel, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.panel = panel

        self.initUI()
        self.initBindings()

    def initUI(self):
        channelTableEditorView = ChannelTableEditorView(self.panel.channels)
        channelTableEditorView.setMinimumHeight(200)
        channelTableEditorView.setMaximumHeight(1000)
        channelTableEditorView.setMaximumWidth(500)
        self.channelTableEditorView = channelTableEditorView

        scrollArea = QScrollArea()
        scrollArea.setWidget(channelTableEditorView)
        scrollArea.setWidgetResizable(True)

        layout = QVBoxLayout()
        layout.addWidget(scrollArea)
        self.setLayout(layout)

    def initBindings(self):
        self.channelTableEditorView.channelListChanged.connect(
            lambda: self.panelChanged.emit()
        )


class PanelListEditorView(QWidget):
    panelListChanged = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.tabWidget = EditableTabWidget(addButtonText="Add new panel")

        layout = QVBoxLayout()
        layout.addWidget(self.tabWidget)
        self.setLayout(layout)

    def addPanel(self, panel: Panel) -> None:
        panelEditor = PanelEditorView(panel)
        panelEditor.panelChanged.connect(lambda: self.panelListChanged.emit())
        self.tabWidget.addTab(panelEditor, panel.name)
        self.tabWidget.setCurrentWidget(panelEditor)

    def deletePanel(self, index: int) -> None:
        self.tabWidget.removeTab(index)

    def styleInvalidTabs(self, indexes: Set[int]) -> None:
        tabBar: QTabBar = self.tabWidget.tabBar()
        for index in range(tabBar.count()):
            tabBar.setTabTextColor(
                index, Color.Red.qc() if index in indexes else Color.Black.qc()
            )

    def refresh(self):
        pass


class PanelListEditor(Editor):
    log = logging.getLogger(__name__)

    panelListChanged = Signal()

    def __init__(self, model: ViewerModel, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.model = model
        self.panels = model.state.panels
        self.view = PanelListEditorView()

        # set up bindings
        self.view.panelListChanged.connect(lambda: self.panelListChanged.emit())
        self.panelListChanged.connect(lambda: self.validate())

        tabWidget = self.view.tabWidget
        tabWidget.addTabButton.clicked.connect(lambda: self.addPanel())
        tabWidget.tabCloseRequested.connect(lambda index: self.deletePanel(index))
        tabWidget.tabMoved.connect(lambda to_, from_: self.movePanel(to_, from_))

        def updateName(index: int) -> None:
            name = tabWidget.tabText(index)
            if self.panels[index].name != name:
                self.panels[index].name = name
                self.panelListChanged.emit()

        tabWidget.editingFinished.connect(lambda index: updateName(index))

        # initialize
        for panel in self.panels:
            self.view.addPanel(panel)
        self.view.tabWidget.setCurrentIndex(0)

        self.validate()

    def addPanel(self) -> None:
        count = self.view.tabWidget.count() + 1
        panel = Panel.from_dict({"name": f"New panel {count}"})
        self.panels.append(panel)
        self.view.addPanel(panel)

        self.panelListChanged.emit()
        self.log.info("New panel added")

    def deletePanel(self, index: int) -> None:
        name = self.panels[index].name or "the current panel"

        response = showYesNoDialog(
            parent=self.view,
            title=f"Delete {name}?",
            text=f"Are you sure you want to delete {name}?",
        )
        if response == QMessageBox.Yes:
            del self.panels[index]
            self.view.deletePanel(index)

            self.panelListChanged.emit()
            self.log.info("Panel deleted")

    def movePanel(self, to_: int, from_: int) -> None:
        (self.panels[to_], self.panels[from_]) = (self.panels[from_], self.panels[to_])

        self.panelListChanged.emit()
        self.log.info(f"Panel moved to {to_} from {from_}")

    def validate(self) -> None:
        invalidPanelIndexes = self.model.state.invalid_panel_indexes()
        self.view.styleInvalidTabs(invalidPanelIndexes)
        self.isValid = len(invalidPanelIndexes) == 0
