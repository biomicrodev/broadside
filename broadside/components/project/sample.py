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
    QRect,
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
    QLineEdit,
)
from natsort import natsort_keygen

from .. import CellState, LineEditItemDelegate
from ...models.block import Sample, Vector, Block


def getCohorts(samples: List[Sample]) -> List[str]:
    cohorts = []
    for sample in samples:
        cohorts.extend(sample.cohorts.keys())
    cohorts = sorted(list(set(cohorts)))
    return cohorts


class SampleTableModel(QAbstractTableModel):
    def __init__(self, block: Block, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.samples: List[Sample] = block.samples
        self.vectors: List[Vector] = block.vectors

    def getItem(self, index: QModelIndex) -> Tuple[str, Any]:
        row = index.row()
        column = index.column()

        if column < len(Sample.keys):
            key = Sample.keys[column]
            value = getattr(self.samples[row], key)
        else:
            cohorts = getCohorts(self.samples)
            key = cohorts[column - len(Sample.keys)]
            value = self.samples[row].cohorts.get(key, "")
        return key, value

    def setItem(self, index: QModelIndex, value: Any) -> bool:
        row = index.row()
        column = index.column()

        if column < len(Sample.keys):
            key = Sample.keys[column]
            type_ = Sample.types[column]

            try:
                value = type_(value)
                # if value hasn't actually changed...
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
            key = cohorts[column - len(Sample.keys)]
            type_ = str
            try:
                value = type_(value)
                # if value hasn't actually changed...
                oldValue = self.samples[row].cohorts.get(key, "")
                if oldValue == value:
                    return False

                self.samples[row].cohorts[key] = value
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
                if (name in otherNames) or (name == "") or (name is None):
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
        self.vectors.append(Vector.from_dict({}))
        self.endInsertRows()

        self.layoutChanged.emit()

    def deleteSample(self, index: int) -> None:
        self.layoutAboutToBeChanged.emit()

        self.beginRemoveRows(QModelIndex(), index, index + 1)
        del self.samples[index]
        del self.vectors[index]
        self.endRemoveRows()

        self.layoutChanged.emit()

    def addCohort(self) -> None:
        self.layoutAboutToBeChanged.emit()

        nCohorts = len(getCohorts(self.samples))
        key = f"Cohort Group {nCohorts + 1}"

        index = self.columnCount()
        self.beginInsertColumns(QModelIndex(), index, index)
        for sample in self.samples:
            sample.cohorts[key] = ""
        self.endInsertColumns()

        self.layoutChanged.emit()

    def deleteCohort(self, index: int) -> None:
        self.layoutAboutToBeChanged.emit()

        # TODO: refactor this whole cohort retrieval logic
        cohorts = getCohorts(self.samples)
        key = cohorts[index - len(Sample.keys)]

        self.beginRemoveColumns(QModelIndex(), index, index)
        for sample in self.samples:
            del sample.cohorts[key]
        self.endRemoveColumns()

        self.layoutChanged.emit()

    def updateCohort(self, column: int, newKey: str) -> None:
        cohorts = getCohorts(self.samples)
        oldKey = cohorts[column - len(Sample.keys)]

        # keys must be unique! really don't like how I'm enforcing this constraint
        # I didn't think ahead on this.
        if oldKey == newKey:
            return

        if newKey in cohorts[len(Sample.keys) :]:
            return

        self.layoutAboutToBeChanged.emit()

        for sample in self.samples:
            cohortValue = sample.cohorts[oldKey]
            del sample.cohorts[oldKey]
            sample.cohorts[newKey] = cohortValue

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


class HeaderView(QHeaderView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setStretchLastSection(True)

        lineEdit = QLineEdit(self.viewport())
        lineEdit.setAlignment(Qt.AlignCenter)
        lineEdit.setHidden(True)
        lineEdit.blockSignals(True)
        lineEdit.editingFinished.connect(self.doneEditing)
        self.lineEdit = lineEdit

        self.sectionEdit = 0

        self.sectionDoubleClicked.connect(self.editHeader)

    def doneEditing(self):
        value = str(self.lineEdit.text())
        self.lineEdit.blockSignals(True)
        self.lineEdit.setHidden(True)
        self.lineEdit.setText("")

        model: SampleTableModel = self.model()
        model.updateCohort(self.sectionEdit, value)

        # purely for focusing reasons
        index: QModelIndex = model.createIndex(0, self.sectionEdit)
        view: SampleTableView = self.parent()
        view.setCurrentIndex(index)

    def editHeader(self, section: int):
        if section < 2:
            return

        model: SampleTableModel = self.model()
        cohorts = getCohorts(model.samples)
        key = cohorts[section - len(Sample.keys)]

        editRect: QRect = self.lineEdit.geometry()
        editRect.setLeft(self.sectionPosition(section))
        editRect.setWidth(self.sectionSize(section))
        editRect.setTop(0)
        editRect.setHeight(self.height())

        self.lineEdit.setText(str(key))
        self.lineEdit.move(editRect.topLeft())
        self.lineEdit.resize(editRect.size())
        self.lineEdit.setFrame(False)
        self.lineEdit.setHidden(False)
        self.lineEdit.blockSignals(False)
        self.lineEdit.setFocus()
        self.lineEdit.selectAll()

        self.sectionEdit = section


class SampleTableView(QTableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setSelectionMode(QAbstractItemView.SingleSelection)

        lineEditDelegate = LineEditItemDelegate(parent=self)
        self.setItemDelegateForColumn(0, lineEditDelegate)

        deviceComboBoxDelegate = DeviceComboBoxDelegate(parent=self)
        self.deviceComboBoxDelegate = deviceComboBoxDelegate
        self.setItemDelegateForColumn(1, deviceComboBoxDelegate)

        horizontalHeader = HeaderView(Qt.Horizontal, self)
        self.setHorizontalHeader(horizontalHeader)


class SampleTableEditorView(QWidget):
    log = logging.getLogger(__name__)

    dataChanged = Signal()

    def __init__(self, block: Block, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.model = SampleTableModel(block)
        self.model.dataChanged.connect(lambda _: self.dataChanged.emit())
        self.model.layoutChanged.connect(lambda: self.dataChanged.emit())

        self.view = SampleTableView()
        self.view.setModel(self.model)

        deviceNamesModel = DeviceNamesModel()
        self.deviceNamesModel = deviceNamesModel
        self.view.deviceComboBoxDelegate.setModel(deviceNamesModel)

        self.initUI()
        self.initReactivity()

    def initUI(self):
        addSampleButton = QPushButton()
        addSampleButton.setText("Add sample")
        self.addSampleButton = addSampleButton

        deleteSampleButton = QPushButton()
        deleteSampleButton.setText("Delete sample")
        deleteSampleButton.setObjectName("deleteSampleButton")
        deleteSampleButton.setDisabled(True)
        self.deleteSampleButton = deleteSampleButton

        sortSamplesButton = QPushButton()
        sortSamplesButton.setText("Sort")
        self.sortSamplesButton = sortSamplesButton

        buttonsLayout = QHBoxLayout()
        buttonsLayout.addWidget(self.addSampleButton)
        buttonsLayout.addWidget(self.deleteSampleButton)
        buttonsLayout.addWidget(self.sortSamplesButton)

        addCohortButton = QPushButton()
        addCohortButton.setText("Add cohort")
        self.addCohortButton = addCohortButton

        deleteCohortButton = QPushButton()
        deleteCohortButton.setText("Delete cohort")
        deleteCohortButton.setObjectName("deleteCohortButton")
        deleteCohortButton.setDisabled(True)
        self.deleteCohortButton = deleteCohortButton

        cohortsButtonsLayout = QHBoxLayout()
        cohortsButtonsLayout.addWidget(self.addCohortButton)
        cohortsButtonsLayout.addWidget(self.deleteCohortButton)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)
        layout.addLayout(buttonsLayout)
        layout.addLayout(cohortsButtonsLayout)

        self.setLayout(layout)

    def initReactivity(self):
        def updateButtons():
            indexes: List[QModelIndex] = self.view.selectedIndexes()

            # enable delete sample button if anything is selected
            nRows = self.model.rowCount()
            indexes = [index for index in indexes if index.row() < nRows]
            self.deleteSampleButton.setEnabled(len(indexes) > 0)

            # enable delete cohort button if cohort columns are selected
            if len(indexes) > 0:
                index: QModelIndex = indexes[0]
                column = index.column()
                self.deleteCohortButton.setEnabled(column >= len(Sample.keys))
            else:
                self.deleteCohortButton.setEnabled(False)

        selectionModel: QItemSelectionModel = self.view.selectionModel()
        selectionModel.selectionChanged.connect(lambda: updateButtons())

        def addSample():
            self.model.addSample()

            # set focus to newly added sample
            row = self.model.rowCount() - 1
            column = 0
            modelIndex = self.model.createIndex(row, column)
            self.view.setCurrentIndex(modelIndex)
            self.view.setFocus()

        self.addSampleButton.clicked.connect(lambda: addSample())

        def deleteSample():
            # after deleting row, need to re-set index
            index: QModelIndex = self.view.selectedIndexes()[0]
            row = index.row()
            column = index.column()

            self.model.deleteSample(row)

            # set focus
            modelIndex = self.model.createIndex(row, column)
            self.view.setCurrentIndex(modelIndex)
            self.view.setFocus()

        self.deleteSampleButton.clicked.connect(lambda: deleteSample())

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

        self.sortSamplesButton.clicked.connect(lambda: sort())

        def updateLineEditItemDelegates():
            nColumns = self.model.columnCount()
            for i in range(len(Sample.keys), nColumns):
                lineEditDelegate = LineEditItemDelegate(parent=self.view)
                self.view.setItemDelegateForColumn(i, lineEditDelegate)

        def addCohort():
            self.model.addCohort()
            updateLineEditItemDelegates()

        self.addCohortButton.clicked.connect(lambda: addCohort())
        updateLineEditItemDelegates()

        def deleteCohort():
            # after deleting row, need to re-set index
            index: QModelIndex = self.view.selectedIndexes()[0]
            self.model.deleteCohort(index.column())

        self.deleteCohortButton.clicked.connect(lambda: deleteCohort())
