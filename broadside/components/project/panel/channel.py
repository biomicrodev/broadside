import logging
from typing import List, Any, Type

from PySide2.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    Qt,
    Signal,
    QAbstractItemModel,
    QItemSelectionModel,
)
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import (
    QTableView,
    QAbstractItemView,
    QHeaderView,
    QWidget,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
)

from ...utils import CellState, LineEditItemDelegate
from ....models.panel import Channel


class ChannelTableModel(QAbstractTableModel):
    def __init__(self, channels: List[Channel], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.channels = channels

    def data(self, index: QModelIndex, role: Qt.ItemDataRole = None) -> Any:
        if role in [Qt.DisplayRole, Qt.EditRole, Qt.ToolTipRole]:
            key = Channel.keys[index.column()]
            value = getattr(self.channels[index.row()], key)

            return str(value) if value is not None else ""

        elif role == Qt.BackgroundRole:
            row = index.row()
            key = Channel.keys[index.column()]
            value = getattr(self.channels[row], key)

            if (key == "biomarker") and ((value == "") or (value is None)):
                return CellState.Invalid

            # are biomarker names unique?
            biomarker = self.channels[row].biomarker
            otherBiomarkers = [
                c.biomarker for i, c in enumerate(self.channels) if i != row
            ]
            if biomarker in otherBiomarkers:
                return CellState.Invalid
            else:
                return CellState.Valid

        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter

    def setData(
        self, index: QModelIndex, value: Any, role: Qt.ItemDataRole = None
    ) -> bool:
        if role == Qt.EditRole:
            row = index.row()
            column = index.column()

            key = Channel.keys[column]
            type_ = Channel.types[column]

            value = type_(value)
            oldValue = getattr(self.channels[row], key)
            if oldValue == value:
                return False

            setattr(self.channels[row], key, value)
            self.dataChanged.emit(QModelIndex(), QModelIndex(), Qt.EditRole)
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
                return section + 1

    def addChannel(self) -> None:
        self.layoutAboutToBeChanged.emit()

        index = self.rowCount()
        self.beginInsertRows(QModelIndex(), index, index)
        self.channels.append(Channel.from_dict({}))
        self.endInsertRows()

        self.layoutChanged.emit()

    def removeChannel(self, index: int) -> None:
        self.layoutAboutToBeChanged.emit()

        self.beginRemoveRows(QModelIndex(), index, index)
        del self.channels[index]
        self.endRemoveRows()

        self.layoutChanged.emit()

    def moveChannelUp(self, index: QModelIndex) -> None:
        self.layoutAboutToBeChanged.emit()

        row = index.row()

        self.beginMoveRows(index, row, row, index, row - 1)
        (self.channels[row - 1], self.channels[row]) = (
            self.channels[row],
            self.channels[row - 1],
        )
        self.endMoveRows()

        self.layoutChanged.emit()

    def moveChannelDown(self, index: QModelIndex) -> None:
        self.layoutAboutToBeChanged.emit()

        row = index.row()

        self.beginMoveRows(index, row, row, index, row + 2)
        (self.channels[row + 1], self.channels[row]) = (
            self.channels[row],
            self.channels[row + 1],
        )
        self.endMoveRows()

        self.layoutChanged.emit()


class ChannelTableView(QTableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setSelectionMode(QAbstractItemView.SingleSelection)
        horizontalHeader: QHeaderView = self.horizontalHeader()
        horizontalHeader.setStretchLastSection(True)

        delegate = LineEditItemDelegate(parent=self)
        self.setItemDelegate(delegate)

    def channelAdded(self) -> None:
        model: Type[QAbstractItemModel] = self.model()

        row = model.rowCount() - 1
        column = 0
        modelIndex: QModelIndex = model.createIndex(row, column)
        self.setCurrentIndex(modelIndex)
        self.setFocus()


class ChannelTableEditorView(QWidget):
    log = logging.getLogger(__name__)

    channelListChanged = Signal()

    def __init__(self, channels: List[Channel], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.model = ChannelTableModel(channels)
        self.model.dataChanged.connect(lambda _: self.channelListChanged.emit())
        self.model.layoutChanged.connect(lambda: self.channelListChanged.emit())

        self.view = ChannelTableView()
        self.view.setModel(self.model)

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

        moveUpIcon = QIcon()
        moveUpIcon.addFile("broadside/resources/icons/chevron_up.svg")
        moveUpButton = QPushButton()
        moveUpButton.setIcon(moveUpIcon)
        moveUpButton.setDisabled(True)
        moveUpButton.setCursor(Qt.ForbiddenCursor)
        self.moveUpButton = moveUpButton

        moveDownIcon = QIcon()
        moveDownIcon.addFile("broadside/resources/icons/chevron_down.svg")
        moveDownButton = QPushButton()
        moveDownButton.setIcon(moveDownIcon)
        moveDownButton.setDisabled(True)
        moveDownButton.setCursor(Qt.ForbiddenCursor)
        self.moveDownButton = moveDownButton

        buttonsLayout = QHBoxLayout()
        buttonsLayout.addWidget(addChannelButton, 1)
        buttonsLayout.addWidget(deleteChannelButton, 1)
        buttonsLayout.addWidget(moveUpButton, 0)
        buttonsLayout.addWidget(moveDownButton, 0)

        layout = QVBoxLayout()
        layout.addWidget(self.view, 1)
        layout.addLayout(buttonsLayout, 0)

        self.setLayout(layout)

    def initBindings(self):
        def addChannel():
            self.model.addChannel()
            self.view.channelAdded()

        self.addChannelButton.clicked.connect(lambda: addChannel())

        def deleteChannel():
            index: QModelIndex = self.view.selectedIndexes()[0]
            self.model.removeChannel(index.row())
            self.updateButtons()

        self.deleteChannelButton.clicked.connect(lambda: deleteChannel())

        def moveChannelUp():
            index: QModelIndex = self.view.selectedIndexes()[0]
            self.model.moveChannelUp(index)

            newIndex = self.model.createIndex(index.row() - 1, index.column())
            self.view.setCurrentIndex(newIndex)

            self.updateButtons()

        self.moveUpButton.clicked.connect(lambda: moveChannelUp())

        def moveChannelDown():
            index: QModelIndex = self.view.selectedIndexes()[0]
            self.model.moveChannelDown(index)

            newIndex = self.model.createIndex(index.row() + 1, index.column())
            self.view.setCurrentIndex(newIndex)

            self.updateButtons()

        self.moveDownButton.clicked.connect(lambda: moveChannelDown())

        selectionModel: QItemSelectionModel = self.view.selectionModel()
        selectionModel.selectionChanged.connect(lambda: self.updateButtons())
        self.updateButtons()

    def updateButtons(self):
        indexes: List[QModelIndex] = self.view.selectedIndexes()
        isSelected = len(indexes) > 0

        self.deleteChannelButton.setEnabled(isSelected)
        self.deleteChannelButton.setCursor(
            Qt.PointingHandCursor if isSelected else Qt.ForbiddenCursor
        )

        if isSelected:
            index: int = indexes[0].row()

            isFirst = index == 0
            isLast = index == (self.model.rowCount() - 1)

            self.moveUpButton.setEnabled(not isFirst)
            self.moveUpButton.setCursor(
                Qt.PointingHandCursor if not isFirst else Qt.ForbiddenCursor
            )
            self.moveDownButton.setEnabled(not isLast)
            self.moveDownButton.setCursor(
                Qt.PointingHandCursor if not isLast else Qt.ForbiddenCursor
            )
        else:
            self.moveUpButton.setEnabled(False)
            self.moveUpButton.setCursor(Qt.ForbiddenCursor)
            self.moveDownButton.setEnabled(False)
            self.moveDownButton.setCursor(Qt.ForbiddenCursor)
