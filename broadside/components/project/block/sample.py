import copy
import logging
from typing import List, Any, Tuple, Type

from qtpy.QtCore import (
    Signal,
    QAbstractTableModel,
    QModelIndex,
    Qt,
    QItemSelectionModel,
    QRect,
    QAbstractItemModel,
)
from qtpy.QtWidgets import (
    QWidget,
    QTableView,
    QAbstractItemView,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QHeaderView,
    QLineEdit,
)
from natsort import natsort_keygen

from ...utils import CellState, LineEditItemDelegate, NamesModel, ComboBoxDelegate
from ....models.block import Sample, Block
from ....models.device import Device, NO_DEVICE


def getCohorts(samples: List[Sample]) -> List[str]:
    def key(name: str) -> Tuple[bool, str]:
        return name == "", name

    natkey = natsort_keygen(key=key)

    cohorts = []
    for sample in samples:
        cohorts.extend(sample.cohorts.keys())
    cohorts = sorted(list(set(cohorts)), key=natkey)
    return cohorts


def getDeviceNames(devices: List[Device]) -> List[str]:
    def key(name: str) -> Tuple[bool, str]:
        return name == "", name

    natkey = natsort_keygen(key=key)
    names = [NO_DEVICE] + sorted([d.name for d in devices], key=natkey)
    return names


class SampleTableModel(QAbstractTableModel):
    def __init__(self, block: Block, devices: List[Device], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.samples: List[Sample] = block.samples
        self.devices = devices

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
        col = index.column()

        # if key is either sample name or device name
        if col < len(Sample.keys):
            key = Sample.keys[col]
            type_ = Sample.types[col]

            value = type_(value)
            oldValue = getattr(self.samples[row], key)
            if oldValue == value:
                return False

            setattr(self.samples[row], key, value)
            self.dataChanged.emit(QModelIndex(), QModelIndex(), Qt.EditRole)
            return True

        # if key is in cohorts
        else:
            cohorts = getCohorts(self.samples)
            key = cohorts[col - len(Sample.keys)]

            value = str(value)
            oldValue = self.samples[row].cohorts.get(key, "")
            if oldValue == value:
                return False

            self.samples[row].cohorts[key] = value
            self.dataChanged.emit(QModelIndex(), QModelIndex(), Qt.EditRole)
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

            elif key == "device_name":
                if value != "":
                    return CellState.Valid
                else:
                    return CellState.Invalid

        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter

    def setData(
        self, index: QModelIndex, value: Any, role: Qt.ItemDataRole = None
    ) -> bool:
        if role == Qt.EditRole:
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
        self.samples.append(Sample.from_dict({"name": f"New sample {index + 1}"}))
        self.endInsertRows()

        self.layoutChanged.emit()

    def deleteSample(self, index: int) -> None:
        self.layoutAboutToBeChanged.emit()

        self.beginRemoveRows(QModelIndex(), index, index + 1)
        del self.samples[index]
        self.endRemoveRows()

        self.layoutChanged.emit()

    def sortSamples(self) -> None:
        natsort = natsort_keygen(
            key=lambda s: (s.name is None, s.device_name is None, s.name, s.device_name)
        )

        oldSamples = copy.copy(self.samples)
        self.samples.sort(key=natsort)
        if self.samples != oldSamples:
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


class SampleTableHeaderView(QHeaderView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setStretchLastSection(True)

        lineEdit = QLineEdit(self.viewport())
        lineEdit.setAlignment(Qt.AlignCenter)
        lineEdit.setHidden(True)
        lineEdit.blockSignals(True)
        lineEdit.editingFinished.connect(self.finishEdit)
        self.lineEdit = lineEdit

        self.sectionEdit = 0

        self.sectionDoubleClicked.connect(self.startEdit)

    def startEdit(self, section: int) -> None:
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

    def finishEdit(self) -> None:
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


class SampleTableView(QTableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setSelectionMode(QAbstractItemView.SingleSelection)

        lineEditDelegate = LineEditItemDelegate(parent=self)
        self.setItemDelegateForColumn(0, lineEditDelegate)

        self.deviceComboBoxDelegate = ComboBoxDelegate(parent=self)
        self.setItemDelegateForColumn(1, self.deviceComboBoxDelegate)

        horizontalHeader = SampleTableHeaderView(Qt.Horizontal, self)
        self.setHorizontalHeader(horizontalHeader)

    def sampleAdded(self) -> None:
        model: Type[QAbstractItemModel] = self.model()

        row = model.rowCount() - 1
        column = 0
        modelIndex = model.createIndex(row, column)
        self.view.setCurrentIndex(modelIndex)
        self.view.setFocus()

    def sampleDeleted(self, index: QModelIndex) -> None:
        model: Type[QAbstractItemModel] = self.model()
        nRows = model.rowCount()
        row = index.row()
        column = index.column()

        if row != nRows:  # row is already deleted
            modelIndex = model.createIndex(row, column)
            self.setCurrentIndex(modelIndex)
            self.setFocus()


class SampleTableEditorView(QWidget):
    log = logging.getLogger(__name__)

    sampleListChanged = Signal()

    def __init__(self, block: Block, devices: List[Device], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.devices = devices

        self.model = SampleTableModel(block, devices)
        self.view = SampleTableView()
        self.view.setModel(self.model)

        self.model.dataChanged.connect(lambda _: self.sampleListChanged.emit())
        self.model.layoutChanged.connect(lambda: self.sampleListChanged.emit())

        deviceNames = getDeviceNames(devices)
        self.deviceNamesModel = NamesModel(deviceNames)
        self.view.deviceComboBoxDelegate.setModel(self.deviceNamesModel)

        self.initUI()
        self.initBindings()

    def initUI(self):
        addSampleButton = QPushButton()
        addSampleButton.setText("Add sample")
        addSampleButton.setCursor(Qt.PointingHandCursor)
        self.addSampleButton = addSampleButton

        deleteSampleButton = QPushButton()
        deleteSampleButton.setText("Delete sample")
        deleteSampleButton.setObjectName("deleteSampleButton")
        deleteSampleButton.setDisabled(True)
        deleteSampleButton.setCursor(Qt.ForbiddenCursor)
        self.deleteSampleButton = deleteSampleButton

        sortSamplesButton = QPushButton()
        sortSamplesButton.setText("Sort")
        sortSamplesButton.setCursor(Qt.PointingHandCursor)
        self.sortSamplesButton = sortSamplesButton

        buttonsLayout = QHBoxLayout()
        buttonsLayout.addWidget(self.addSampleButton)
        buttonsLayout.addWidget(self.deleteSampleButton)
        buttonsLayout.addWidget(self.sortSamplesButton)

        addCohortButton = QPushButton()
        addCohortButton.setText("Add cohort")
        addCohortButton.setCursor(Qt.PointingHandCursor)
        self.addCohortButton = addCohortButton

        deleteCohortButton = QPushButton()
        deleteCohortButton.setText("Delete cohort")
        deleteCohortButton.setObjectName("deleteCohortButton")
        deleteCohortButton.setDisabled(True)
        deleteCohortButton.setCursor(Qt.ForbiddenCursor)
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

    def initBindings(self):
        # delegates
        def updateLineEditItemDelegates():
            nColumns = self.model.columnCount()
            for i in range(len(Sample.keys), nColumns):
                lineEditDelegate = LineEditItemDelegate(parent=self.view)
                self.view.setItemDelegateForColumn(i, lineEditDelegate)

        updateLineEditItemDelegates()

        def addSample():
            self.model.addSample()
            self.view.sampleAdded()

        self.addSampleButton.clicked.connect(lambda: addSample())

        def deleteSample():
            index: QModelIndex = self.view.selectedIndexes()[0]
            row = index.row()

            self.model.deleteSample(row)
            self.view.sampleDeleted(index)
            self.updateButtons()

        self.deleteSampleButton.clicked.connect(lambda: deleteSample())

        self.sortSamplesButton.clicked.connect(lambda: self.model.sortSamples())

        def addCohort():
            self.model.addCohort()
            updateLineEditItemDelegates()

        self.addCohortButton.clicked.connect(lambda: addCohort())

        def deleteCohort():
            # after deleting row, need to re-set index
            index: QModelIndex = self.view.selectedIndexes()[0]
            self.model.deleteCohort(index.column())

        self.deleteCohortButton.clicked.connect(lambda: deleteCohort())

        selectionModel: QItemSelectionModel = self.view.selectionModel()
        selectionModel.selectionChanged.connect(lambda: self.updateButtons())
        self.updateButtons()

    def updateButtons(self) -> None:
        indexes: List[QModelIndex] = self.view.selectedIndexes()

        # enable delete sample button if anything is selected
        self.deleteSampleButton.setEnabled(len(indexes) > 0)
        self.deleteSampleButton.setCursor(
            Qt.PointingHandCursor if (len(indexes) > 0) else Qt.ForbiddenCursor
        )

        # enable delete cohort button if cohort columns are selected
        if len(indexes) > 0:
            index: QModelIndex = indexes[0]
            column = index.column()
            self.deleteCohortButton.setEnabled(column >= len(Sample.keys))
            self.deleteCohortButton.setCursor(
                Qt.PointingHandCursor
                if (column >= len(Sample.keys))
                else Qt.ForbiddenCursor
            )
        else:
            self.deleteCohortButton.setEnabled(False)
            self.deleteCohortButton.setCursor(Qt.ForbiddenCursor)

    def refresh(self) -> None:
        deviceNames = getDeviceNames(self.devices)
        self.deviceNamesModel.updateNames(deviceNames)
        self.deviceNamesModel.layoutChanged.emit()
