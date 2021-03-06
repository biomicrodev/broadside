import logging
from typing import Set

from qtpy.QtGui import QColor
from qtpy.QtWidgets import QWidget, QTabBar, QVBoxLayout, QMessageBox, QScrollArea

from .channels import ChannelsEditorView, ChannelsEditor
from ....editor import Editor
from ....utils import EditableTabWidget, showYesNoDialog
from ....viewer_model import ViewerModel
from .....models.panel import Panel, Channel
from .....utils.colors import Color


class PanelEditorView(QWidget):
    def __init__(self, channelsEditorView: ChannelsEditorView, *args, **kwargs):
        super().__init__(*args, **kwargs)

        scrollArea = QScrollArea()
        scrollArea.setWidget(channelsEditorView)
        scrollArea.setWidgetResizable(True)

        parentLayout = QVBoxLayout()
        parentLayout.addWidget(scrollArea, 1)
        self.setLayout(parentLayout)


class PanelEditor:
    def __init__(self, channels_editor_view: ChannelsEditorView):
        self._view = PanelEditorView(channelsEditorView=channels_editor_view)


class PanelsEditorView(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.tabWidget = EditableTabWidget(addButtonText="Add new panel")

        layout = QVBoxLayout()
        layout.addWidget(self.tabWidget)
        self.setLayout(layout)

    def styleInvalidTabs(self, indexes: Set[int]) -> None:
        tabBar: QTabBar = self.tabWidget.tabBar()
        for index in range(tabBar.count()):
            tabBar.setTabTextColor(
                index, QColor(*(Color.red if index in indexes else Color.Black).value)
            )


class PanelsEditor(Editor):
    log = logging.getLogger(__name__)

    def __init__(self, model: ViewerModel):
        super().__init__()

        self.state = model.state
        self._view = PanelsEditorView()

        panels = self.state.panels
        panels.events.changed.connect(lambda _: self.validate())
        panels.events.added.connect(lambda d: self.panel_added(d["item"]))
        panels.events.deleted.connect(self.panel_deleted)

        # bindings from view to model
        tab_widget = self._view.tabWidget
        tab_widget.addTabButton.clicked.connect(lambda _: self.add_panel())
        tab_widget.tabCloseRequested.connect(self.ask_delete_panel)
        tab_widget.tabMoved.connect(panels.swap)

        def update_name(index: int) -> None:
            name = tab_widget.tabText(index)
            panel: Panel = panels[index]
            panel.name = name

        tab_widget.editingFinished.connect(update_name)

        # initialize
        for panel in panels:
            self._add_panel_bindings(panel)
            self.panel_added(panel)
        self._view.tabWidget.setCurrentIndex(0)

        self.validate()

    def panel_added(self, panel: Panel):
        channels_editor = ChannelsEditor(panel.channels)

        panel_editor = PanelEditor(channels_editor_view=channels_editor._view)
        self._view.tabWidget.addTab(panel_editor._view, panel.name)
        self._view.tabWidget.setCurrentWidget(panel_editor._view)

    def panel_deleted(self, index: int) -> None:
        self._view.tabWidget.removeTab(index)

    def add_panel(self):
        n_panels = len(self.state.panels)
        panel = Panel(name=f"New panel {n_panels + 1}")
        self.state.panels.append(panel)
        self._add_panel_bindings(panel)

    def _add_panel_bindings(self, panel: Panel):
        panel.events.name.connect(lambda _: self.validate())

        def add_channel_bindings(channel: Channel):
            channel.events.biomarker.connect(lambda _: self.validate())
            channel.events.chromogen.connect(lambda _: self.validate())
            channel.events.notes.connect(lambda _: self.validate())

        panel.channels.events.added.connect(lambda d: add_channel_bindings(d["item"]))
        panel.channels.events.changed.connect(lambda _: self.validate())
        for channel in panel.channels:
            add_channel_bindings(channel)

    def ask_delete_panel(self, index: int) -> None:
        name = self._view.tabWidget.tabText(index) or f"panel {index + 1}"
        response = showYesNoDialog(
            parent=self._view,
            title=f"Delete {name}?",
            text=f"Are you sure you want to delete {name}?",
        )
        if response != QMessageBox.Yes:
            return

        del self.state.panels[index]
        self.log.debug(f"Panel {name} deleted")

    def validate(self) -> None:
        invalid_panel_indexes = self.state.invalid_panel_indexes()
        self._view.styleInvalidTabs(invalid_panel_indexes)
        self.is_valid = len(invalid_panel_indexes) == 0
