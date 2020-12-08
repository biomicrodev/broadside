import logging
from typing import List, Any

from PySide2.QtCore import (
    Signal,
    QAbstractTableModel,
    QModelIndex,
    Qt,
    QItemSelectionModel,
    QRect,
)
from PySide2.QtGui import QPainter, QPen
from PySide2.QtWidgets import (
    QWidget,
    QTableView,
    QHeaderView,
    QAbstractItemView,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QStyledItemDelegate,
    QLineEdit,
    QStyleOptionViewItem,
)
from natsort import natsort_keygen

from .. import CellState
from ...color import Color
from ...models.samplegroup import Sample


class SampleTableModel(QAbstractTableModel):
    def __init__(self, samples: List[Sample], cohorts: List[str], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.samples = samples
        self.cohorts = cohorts

    def data(self, index: QModelIndex, role: Qt.ItemDataRole = None) -> Any:
        if role in [Qt.DisplayRole, Qt.EditRole, Qt.ToolTipRole]:
            column = index.column()
            if column < len(Sample.keys):
                key = Sample.keys[column]
                value = getattr(self.samples[index.row()], key)
            else:
                key = self.cohorts[column]
                value = self.samples[index.row()].cohorts[key]

            if value is None:
                return ""
            else:
                return str(value)

        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter

    def setData(
        self, index: QModelIndex, value: Any, role: Qt.ItemDataRole = None
    ) -> bool:
        if role == Qt.EditRole:
            if not index.isValid():
                return False

        return False

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        return super().flags(index) | Qt.ItemIsEditable

    def rowCount(self, parent: QModelIndex = None, *args, **kwargs) -> int:
        return len(self.samples)

    def columnCount(self, parent: QModelIndex = None, *args, **kwargs) -> int:
        return len(Sample.keys) + len(self.cohorts)

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole = None
    ) -> Any:
        if role == Qt.DisplayRole:
            # column headers
            if orientation == Qt.Horizontal:
                return (list(Sample.headers) + self.cohorts)[section]

            # row headers
            elif orientation == Qt.Vertical:
                return section + 1  # section is 0-indexed

    def addSample(self):
        self.layoutAboutToBeChanged.emit()

        index = self.rowCount()
        self.beginInsertRows(QModelIndex(), index, index)
        self.samples.append(Sample.from_dict({}))
        self.endInsertRows()

        self.layoutChanged.emit()

    def removeSample(self, index):
        self.layoutAboutToBeChanged.emit()

        self.beginRemoveRows(QModelIndex(), index, index)
        del self.samples[index]
        self.endRemoveRows()

        modelIndex = self.createIndex(index, 0)
        self.changePersistentIndex(modelIndex, modelIndex)
        self.layoutChanged.emit()


class LineEditItemDelegate(QStyledItemDelegate):
    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ) -> QWidget:
        editor = QLineEdit(parent=parent)
        editor.setAlignment(Qt.AlignCenter)
        return editor

    def paint(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex
    ) -> None:
        super().paint(painter, option, index)

        cellState: CellState = index.data(Qt.BackgroundRole)
        if cellState == CellState.Invalid:
            padding = 0
            x = option.rect.x() + padding
            y = option.rect.y() + padding
            w = option.rect.width() - 1 - padding
            h = option.rect.height() - 1 - padding

            pen = QPen()
            pen.setColor(Color.Red.qc())
            pen.setWidth(1)

            painter.setPen(pen)
            painter.drawRect(QRect(x, y, w, h))


class SampleTableView(QTableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setSelectionMode(QAbstractItemView.SingleSelection)
        horizontalHeader: QHeaderView = self.horizontalHeader()
        horizontalHeader.setStretchLastSection(True)


class SampleTableEditorView(QWidget):
    log = logging.getLogger(__name__)

    dataChanged = Signal()

    def __init__(self, samples: List[Sample], cohorts: List[str], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.model = SampleTableModel(samples=samples, cohorts=cohorts)
        self.model.dataChanged.connect(lambda _: self.dataChanged.emit())
        self.model.layoutChanged.connect(lambda: self.dataChanged.emit())

        self.view = SampleTableView()
        self.view.setModel(self.model)

        def addSample():
            self.model.addSample()

            row = self.model.rowCount() - 1
            column = 0
            modelIndex = self.model.createIndex(row, column)
            self.view.setCurrentIndex(modelIndex)
            self.view.setFocus()

        addSampleButton = QPushButton()
        addSampleButton.setText("Add sample")
        addSampleButton.clicked.connect(lambda: addSample())
        self.addSampleButton = addSampleButton

        def deleteSample():
            # after deleting row, need to re-set index
            index: QModelIndex = self.view.selectedIndexes()[0]
            row = index.row()
            column = index.column()

            self.model.removeSample(row)

            modelIndex = self.model.createIndex(row, column)
            self.view.setCurrentIndex(modelIndex)
            self.view.setFocus()

        deleteSampleButton = QPushButton()
        deleteSampleButton.setText("Delete sample")
        deleteSampleButton.setObjectName("deleteSampleButton")
        deleteSampleButton.setDisabled(True)
        deleteSampleButton.clicked.connect(lambda: deleteSample())
        self.deleteSampleButton = deleteSampleButton

        def selectionChanged():
            indexes = self.view.selectedIndexes()
            nRows = self.model.rowCount()
            indexes = [index for index in indexes if index.row() < nRows]
            self.deleteSampleButton.setEnabled(len(indexes) > 0)

        selectionModel: QItemSelectionModel = self.view.selectionModel()
        selectionModel.selectionChanged.connect(lambda: selectionChanged())

        natsort = natsort_keygen(
            key=lambda s: (s.name is None, s.deviceName is None, s.name, s.deviceName)
        )

        def sort():
            self.model.samples.sort(key=natsort)
            self.model.layoutChanged.emit()

        sortSamplesButton = QPushButton()
        sortSamplesButton.setText("Sort")
        sortSamplesButton.clicked.connect(lambda: sort())
        self.sortSamplesButton = sortSamplesButton

        buttonsLayout = QHBoxLayout()
        buttonsLayout.addWidget(self.addSampleButton)
        buttonsLayout.addWidget(self.deleteSampleButton)
        buttonsLayout.addWidget(self.sortSamplesButton)

        layout = QVBoxLayout()
        layout.addWidget(self.view)
        layout.addLayout(buttonsLayout)

        self.setLayout(layout)
