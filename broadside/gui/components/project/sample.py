import copy
import logging
from typing import List, Any, Tuple

from PySide2.QtCore import (
    Signal,
    QAbstractTableModel,
    QModelIndex,
    Qt,
    QItemSelectionModel,
    QAbstractListModel,
)
from PySide2.QtWidgets import (
    QWidget,
    QTableView,
    QHeaderView,
    QAbstractItemView,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QComboBox,
)
from natsort import natsort_keygen

from .. import CellState, LineEditItemDelegate
from ...models.block import Sample


def getCohorts(samples: List[Sample]) -> List[str]:
    cohorts = []
    for sample in samples:
        cohorts.extend(sample.cohorts.keys())
    cohorts = list(set(cohorts))
    return cohorts


class SampleTableModel(QAbstractTableModel):
    def __init__(self, samples: List[Sample], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.samples = samples

    def getItem(self, index: QModelIndex) -> Tuple[str, Any]:
        row = index.row()
        column = index.column()

        if column < len(Sample.keys):
            key = Sample.keys[column]
            value = getattr(self.samples[row], key)
        else:
            cohorts = getCohorts(self.samples)
            key = cohorts[column]
            value = self.samples[row].cohorts[key]
        return key, value

    def setItem(self, index: QModelIndex, value: Any) -> bool:
        row = index.row()
        column = index.column()

        if column < len(Sample.keys):
            key = Sample.keys[column]
            type_ = Sample.types[column]

            try:
                value = type_(value)
                if getattr(self.samples[row], key) == value:
                    return False

                setattr(self.samples[row], key, value)
                self.dataChanged.emit(QModelIndex(), QModelIndex(), Qt.EditRole)
            except ValueError:
                return False
            else:
                return True

        else:
            cohorts = getCohorts(self.samples)
            key = cohorts[column]
            type_ = str
            try:
                self.samples[row].cohorts[key] = type_(value)
                self.dataChanged.emit(QModelIndex(), QModelIndex(), Qt.EditRole)
            except ValueError:
                return False
            else:
                return True

    def data(self, index: QModelIndex, role: Qt.ItemDataRole = None) -> Any:
        if role in [Qt.DisplayRole, Qt.EditRole, Qt.ToolTipRole]:
            key, value = self.getItem(index)
            return str(value) if value is not None else ""

        elif role == Qt.BackgroundRole:
            key, value = self.getItem(index)
            if key == "name":
                # which sample names are not unique?
                name = value
                otherNames = [
                    s.name for i, s in enumerate(self.samples) if i != index.row()
                ]
                if name in otherNames:
                    return CellState.Invalid
                else:
                    return CellState.Valid

            if (value == "") or (value is None):
                return CellState.Invalid
            else:
                return CellState.Valid

        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter

    def setData(
        self, index: QModelIndex, value: Any, role: Qt.ItemDataRole = None
    ) -> bool:
        if role == Qt.EditRole:
            if not index.isValid():
                return False

            key, _ = self.getItem(index)
            if key == "name":
                name = value
                otherNames = [
                    s.name for i, s in enumerate(self.samples) if i != index.row()
                ]
                if name in otherNames:
                    return False
                else:
                    return self.setItem(index, value)

            return self.setItem(index, value)

        return False

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        return super().flags(index) | Qt.ItemIsEditable

    def rowCount(self, parent: QModelIndex = None, *args, **kwargs) -> int:
        return len(self.samples)

    def columnCount(self, parent: QModelIndex = None, *args, **kwargs) -> int:
        cohorts = getCohorts(self.samples)
        return len(Sample.keys) + len(cohorts)

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole = None
    ) -> Any:
        if role == Qt.DisplayRole:
            # column headers
            if orientation == Qt.Horizontal:
                cohorts = getCohorts(self.samples)
                return (list(Sample.headers) + cohorts)[section]

            # row headers
            elif orientation == Qt.Vertical:
                return section + 1  # section is 0-indexed

        elif role == Qt.EditRole:
            if orientation == Qt.Horizontal:
                return Qt.ItemIsEditable

    def addSample(self):
        self.layoutAboutToBeChanged.emit()

        index = self.rowCount()
        self.beginInsertRows(QModelIndex(), index, index)
        self.samples.append(Sample.from_dict({}))
        self.endInsertRows()

        self.layoutChanged.emit()

    def removeSample(self, index: int) -> None:
        self.layoutAboutToBeChanged.emit()

        self.beginRemoveRows(QModelIndex(), index, index + 1)
        del self.samples[index]
        self.endRemoveRows()

        # modelIndex = self.createIndex(index, 0)
        # self.changePersistentIndex(modelIndex, modelIndex)
        self.layoutChanged.emit()

    def addMetadata(self) -> None:
        self.layoutAboutToBeChanged.emit()

        key = "Metadata1"

        index = self.columnCount()
        self.beginInsertColumns(QModelIndex, index, index)
        for sample in self.samples:
            sample.cohorts[key] = ""
        self.endInsertColumns()

        self.layoutChanged.emit()


class DeviceNamesModel(QAbstractListModel):
    def __init__(self, names: List[str] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.names = names or []

    def data(self, index: QModelIndex, role: Qt.ItemDataRole = None) -> Any:
        if role in [Qt.DisplayRole, Qt.EditRole, Qt.ToolTipRole]:
            return str(self.names[index.row()])

        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter

    def updateNames(self, names: List[str]) -> None:
        if self.names == names:
            return

        self.layoutAboutToBeChanged.emit()

        self.names.clear()
        self.names.extend(names)

        self.layoutChanged.emit()

    def rowCount(self, parent: QModelIndex = None, *args, **kwargs) -> int:
        return len(self.names)


class DeviceComboBoxDelegate(QStyledItemDelegate):
    """
    Annoying things to fix here:
    1. When editing the QComboBox delegate's selection, it's not centered
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = None

    def setModel(self, model: QAbstractListModel) -> None:
        self.model = model

    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ) -> QWidget:
        editor = QComboBox(parent=parent)

        if self.model is not None:
            editor.setModel(self.model)

        return editor


class SampleTableView(QTableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # self.setEditTriggers(QAbstractItemView.AllEditTriggers)

        self.setSelectionMode(QAbstractItemView.SingleSelection)
        horizontalHeader: QHeaderView = self.horizontalHeader()
        horizontalHeader.setStretchLastSection(True)

        lineEditDelegate = LineEditItemDelegate(parent=self)
        self.setItemDelegateForColumn(0, lineEditDelegate)

        deviceComboBoxDelegate = DeviceComboBoxDelegate(parent=self)
        self.deviceComboBoxDelegate = deviceComboBoxDelegate
        self.setItemDelegateForColumn(1, deviceComboBoxDelegate)


class SampleTableEditorView(QWidget):
    log = logging.getLogger(__name__)

    dataChanged = Signal()

    def __init__(self, samples: List[Sample], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.model = SampleTableModel(samples)
        self.model.dataChanged.connect(lambda _: self.dataChanged.emit())
        self.model.layoutChanged.connect(lambda: self.dataChanged.emit())

        self.view = SampleTableView()
        self.view.setModel(self.model)

        deviceNamesModel = DeviceNamesModel()
        self.deviceNamesModel = deviceNamesModel
        self.view.deviceComboBoxDelegate.setModel(deviceNamesModel)

        def updateButtons():
            indexes = self.view.selectedIndexes()
            nRows = self.model.rowCount()
            indexes = [index for index in indexes if index.row() < nRows]
            self.deleteSampleButton.setEnabled(len(indexes) > 0)

        selectionModel: QItemSelectionModel = self.view.selectionModel()
        selectionModel.selectionChanged.connect(lambda: updateButtons())

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

        natsort = natsort_keygen(
            key=lambda s: (s.name is None, s.deviceName is None, s.name, s.deviceName)
        )

        def sort():
            # copying like this is okay since this list won't ever be more than 40
            # samples
            oldSamples = copy.copy(self.model.samples)
            self.model.samples.sort(key=natsort)
            if self.model.samples != oldSamples:
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
