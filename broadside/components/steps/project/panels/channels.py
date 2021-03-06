import copy
import logging
from typing import Any, List, Tuple

from natsort import natsort_keygen
from qtpy.QtCore import QAbstractTableModel, QModelIndex, Qt, QItemSelectionModel
from qtpy.QtWidgets import (
    QWidget,
    QTableView,
    QAbstractItemView,
    QHeaderView,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QGroupBox,
)

from ....utils import CellState, LineEditItemDelegate
from .....models.panel import Channel
from .....utils.events import EventedList


class ChannelsTableModel(QAbstractTableModel):
    def __init__(self, channels: EventedList[Channel], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.channels = channels

    def data(self, index: QModelIndex, role: Qt.ItemDataRole = None) -> Any:
        if role in [Qt.DisplayRole, Qt.EditRole, Qt.ToolTipRole]:
            key = Channel.keys[index.column()]
            value = getattr(self.channels[index.row()], key)
            return value
        elif role == Qt.BackgroundRole:
            row = index.row()
            key = Channel.keys[index.column()]
            value = getattr(self.channels[row], key)

            if key in ["biomarker"] and (value == ""):
                return CellState.Invalid

            # are biomarker names unique?
            biomarker = self.channels[row].biomarker
            otherBiomarkers = [
                c.biomarker for i, c in enumerate(self.channels) if i != row
            ]
            if biomarker in otherBiomarkers:
                return CellState.Invalid

            # otherwise...
            return CellState.Valid

        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter

    def setData(
        self, index: QModelIndex, value: Any, role: Qt.ItemDataRole = None
    ) -> bool:
        if role == Qt.EditRole:
            row = index.row()
            col = index.column()

            key = Channel.keys[col]
            type_ = Channel.types[col]

            try:
                value = type_(value)
            except ValueError:
                return False

            setattr(self.channels[row], key, value)
            self.dataChanged.emit(index, index, [Qt.EditRole])
            return True

        return False

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        return super().flags(index) | Qt.ItemIsEditable

    def rowCount(self, parent: QModelIndex = None, *args, **kwargs) -> int:
        return len(self.channels)

    def columnCount(self, parent: QModelIndex = None, *args, **kwargs) -> int:
        return len(Channel.keys)

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole = None
    ) -> Any:
        if role == Qt.DisplayRole:
            # column headers
            if orientation == Qt.Horizontal:
                return Channel.headers[section]

            # row headers
            elif orientation == Qt.Vertical:
                return section + 1  # section is 0-indexed


class ChannelsTableView(QTableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setSelectionMode(QAbstractItemView.SingleSelection)
        horizontalHeader: QHeaderView = self.horizontalHeader()
        horizontalHeader.setStretchLastSection(True)

        delegate = LineEditItemDelegate(parent=self)
        self.setItemDelegate(delegate)


class ChannelsEditorView(QWidget):
    def __init__(self, tableView: ChannelsTableView, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.tableView = tableView

        self.initUI()
        self.initBindings()

    def initUI(self):
        addChannelButton = QPushButton()
        addChannelButton.setText("Add channel")
        addChannelButton.setCursor(Qt.PointingHandCursor)
        self.addChannelButton = addChannelButton

        deleteChannelButton = QPushButton()
        deleteChannelButton.setText("Delete channel")
        deleteChannelButton.setObjectName("deleteChannelButton")
        deleteChannelButton.setDisabled(True)
        deleteChannelButton.setCursor(Qt.ForbiddenCursor)
        self.deleteChannelButton = deleteChannelButton

        sortChannelButton = QPushButton()
        sortChannelButton.setText("Sort")
        sortChannelButton.setCursor(Qt.PointingHandCursor)
        self.sortChannelButton = sortChannelButton

        buttonsLayout = QHBoxLayout()
        buttonsLayout.addWidget(addChannelButton)
        buttonsLayout.addWidget(deleteChannelButton)
        buttonsLayout.addWidget(sortChannelButton)

        layout = QVBoxLayout()
        layout.addWidget(self.tableView, 1)
        layout.addLayout(buttonsLayout, 0)

        groupBox = QGroupBox()
        groupBox.setTitle("Channels")
        groupBox.setLayout(layout)

        parentLayout = QVBoxLayout()
        parentLayout.addWidget(groupBox)
        self.setLayout(parentLayout)

    def initBindings(self):
        selectionModel: QItemSelectionModel = self.tableView.selectionModel()
        selectionModel.selectionChanged.connect(lambda: self.updateButtons())

    def updateButtons(self):
        indexes: List[int] = self.tableView.selectedIndexes()
        self.deleteChannelButton.setEnabled(len(indexes) > 0)
        self.deleteChannelButton.setCursor(
            Qt.PointingHandCursor if (len(indexes) > 0) else Qt.ForbiddenCursor
        )


def channel_key(c: Channel) -> Tuple[bool, str]:
    return (c.biomarker == ""), c.biomarker


class ChannelsEditor:
    log = logging.getLogger(__name__)

    def __init__(self, channels: EventedList[Channel]):
        self.channels = channels

        # set up Qt model/view
        self._model = ChannelsTableModel(channels)
        table_view = ChannelsTableView()
        table_view.setModel(self._model)
        self._view = ChannelsEditorView(table_view)
        self._view.setMaximumWidth(600)
        self._view.setMinimumHeight(300)

        # bindings from view to model
        self._view.addChannelButton.clicked.connect(lambda: self.add_channel())
        self._view.deleteChannelButton.clicked.connect(lambda: self.delete_channel())
        self._view.sortChannelButton.clicked.connect(lambda: self.sort_channels())

        # bindings from model to view
        self.channels.events.changed.connect(lambda _: self._view.updateButtons())

    def add_channel(self):
        # update model
        row = len(self.channels)

        index = self._model.createIndex(row, 0)
        self._model.layoutAboutToBeChanged.emit()
        self._model.beginInsertRows(index, row, row)

        self.channels.append(Channel(biomarker=f"Biomarker {row + 1}"))

        self._model.endInsertRows()
        self._model.layoutChanged.emit()

        # update view
        self._view.tableView.setCurrentIndex(index)
        self._view.tableView.setFocus()

    def delete_channel(self):
        indexes: List[QModelIndex] = self._view.tableView.selectedIndexes()
        index = indexes[0]  # selection model guarantees exactly one selection
        row = index.row()

        # update model
        self._model.layoutAboutToBeChanged.emit()
        self._model.beginRemoveRows(index, row, row)

        del self.channels[row]

        self._model.endRemoveRows()
        self._model.layoutChanged.emit()

        # update view
        if row >= len(self.channels):
            self._view.tableView.clearSelection()
        else:
            self._view.tableView.setCurrentIndex(index)
            self._view.tableView.setFocus()

    def sort_channels(self):
        natkey = natsort_keygen(key=channel_key)

        old_channels = copy.copy(self.channels)
        self.channels.sort(key=natkey)
        if self.channels != old_channels:
            self._model.layoutChanged.emit()
