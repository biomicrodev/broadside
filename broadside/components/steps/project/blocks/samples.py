import copy
from typing import List, Any, Tuple

from natsort import natsort_keygen
from qtpy.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    Qt,
    QRect,
    QItemSelectionModel,
    Signal,
)
from qtpy.QtWidgets import (
    QWidget,
    QTableView,
    QAbstractItemView,
    QHeaderView,
    QLineEdit,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QGroupBox,
)

from ....utils import CellState, LineEditItemDelegate
from .....models.block import Sample
from .....utils.events import EventedList


def sample_key(s: Sample) -> Tuple[bool, str]:
    return (s.name == ""), (s.name)


def get_cohort_names(samples: EventedList[Sample]) -> List[str]:
    def key(name: str) -> Tuple[bool, str]:
        return name == "", name

    natkey = natsort_keygen(key=key)

    cohort_names = []
    for sample in samples:
        cohort_names.extend(sample.cohorts.keys())

    # TODO: remember order here in the future?
    cohort_names = sorted(list(set(cohort_names)), key=natkey)
    return cohort_names


class SamplesTableModel(QAbstractTableModel):
    def __init__(self, samples: EventedList[Sample], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.samples = samples

    def getItem(self, index: QModelIndex) -> Tuple[str, Any]:
        row = index.row()
        column = index.column()

        if column < len(Sample.keys):
            key = Sample.keys[column]
            value = getattr(self.samples[row], key)
        else:
            cohorts = get_cohort_names(self.samples)
            key = cohorts[column - len(Sample.keys)]
            value = self.samples[row].cohorts.get(key, "")
        return key, value

    def setItem(self, index: QModelIndex, value: Any) -> bool:
        row = index.row()
        col = index.column()

        # if key is sample name
        if col < len(Sample.keys):
            key = Sample.keys[col]
            type_ = Sample.types[col]

            value = type_(value)
            oldValue = getattr(self.samples[row], key)
            if oldValue == value:
                return False

            setattr(self.samples[row], key, value)
            self.dataChanged.emit(index, index, [Qt.EditRole])
            return True

        # if key is in cohorts
        else:
            cohorts = get_cohort_names(self.samples)
            key = cohorts[col - len(Sample.keys)]

            value = str(value)
            oldValue = self.samples[row].cohorts.get(key, "")
            if oldValue == value:
                return False

            self.samples[row].cohorts[key] = value
            self.dataChanged.emit(index, index, [Qt.EditRole])
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
        cohorts = get_cohort_names(self.samples)
        return len(Sample.keys) + len(cohorts)

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole = None
    ) -> Any:
        if role == Qt.DisplayRole:
            # column headers
            if orientation == Qt.Horizontal:
                cohorts = get_cohort_names(self.samples)
                return (list(Sample.headers) + cohorts)[section]

            # row headers
            elif orientation == Qt.Vertical:
                return section + 1  # section is 0-indexed

        elif role == Qt.EditRole:
            if orientation == Qt.Horizontal:
                return Qt.ItemIsEditable


class SampleTableHeaderView(QHeaderView):
    editingFinished = Signal(int, str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setHighlightSections(True)
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
        if section < len(Sample.keys):
            return

        pad = 2

        model: SamplesTableModel = self.model()
        cohorts = get_cohort_names(model.samples)
        key = cohorts[section - len(Sample.keys)]

        editRect: QRect = self.lineEdit.geometry()
        editRect.setLeft(self.sectionViewportPosition(section) + pad)
        editRect.setWidth(self.sectionSize(section) - 2 * pad)
        editRect.setTop(pad)
        editRect.setHeight(self.height() - 2 * pad)

        self.lineEdit.setText(str(key))
        self.lineEdit.move(editRect.topLeft())
        self.lineEdit.resize(editRect.size())
        self.lineEdit.setFrame(False)
        self.lineEdit.setHidden(False)
        self.lineEdit.setFocus()
        self.lineEdit.selectAll()
        self.lineEdit.blockSignals(False)

        self.sectionEdit = section

    def finishEdit(self) -> None:
        value = str(self.lineEdit.text())
        self.lineEdit.blockSignals(True)
        self.lineEdit.setHidden(True)
        self.lineEdit.setText("")

        self.editingFinished.emit(self.sectionEdit, value)


class SamplesTableView(QTableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setSelectionMode(QAbstractItemView.SingleSelection)

        lineEditDelegate = LineEditItemDelegate(parent=self)
        self.setItemDelegate(lineEditDelegate)

        horizontalHeader = SampleTableHeaderView(Qt.Horizontal, self)
        self.setHorizontalHeader(horizontalHeader)


class SamplesEditorView(QWidget):
    def __init__(self, tableView: SamplesTableView, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.tableView = tableView

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

        sampleButtonsLayout = QHBoxLayout()
        sampleButtonsLayout.addWidget(self.addSampleButton)
        sampleButtonsLayout.addWidget(self.deleteSampleButton)
        sampleButtonsLayout.addWidget(self.sortSamplesButton)

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

        cohortButtonsLayout = QHBoxLayout()
        cohortButtonsLayout.addWidget(self.addCohortButton)
        cohortButtonsLayout.addWidget(self.deleteCohortButton)

        layout = QVBoxLayout()
        layout.addWidget(self.tableView)
        layout.addLayout(sampleButtonsLayout)
        layout.addLayout(cohortButtonsLayout)

        groupBox = QGroupBox()
        groupBox.setTitle("Samples")
        groupBox.setLayout(layout)

        parentLayout = QVBoxLayout()
        parentLayout.addWidget(groupBox)
        self.setLayout(parentLayout)

    def initBindings(self):
        selectionModel: QItemSelectionModel = self.tableView.selectionModel()
        selectionModel.selectionChanged.connect(lambda: self.updateButtons())

    def updateButtons(self):
        indexes: List[QModelIndex] = self.tableView.selectedIndexes()
        indexes = [index for index in indexes if index.isValid()]
        isSelected = len(indexes) > 0

        # samples
        self.deleteSampleButton.setEnabled(isSelected)
        self.deleteSampleButton.setCursor(
            Qt.PointingHandCursor if isSelected else Qt.ForbiddenCursor
        )

        # cohorts
        if isSelected:
            index: QModelIndex = indexes[0]
            col = index.column()
            self.deleteCohortButton.setEnabled(col >= len(Sample.keys))
            self.deleteCohortButton.setCursor(
                Qt.PointingHandCursor
                if (col >= len(Sample.keys))
                else Qt.ForbiddenCursor
            )
        else:
            self.deleteCohortButton.setEnabled(False)
            self.deleteCohortButton.setCursor(Qt.ForbiddenCursor)


class SamplesEditor:
    def __init__(self, samples: EventedList[Sample]):
        self.samples = samples

        # set up Qt model/view
        self._model = SamplesTableModel(samples)
        table_view = SamplesTableView()
        table_view.setModel(self._model)
        self._view = SamplesEditorView(table_view)

        # bindings from view to model
        self._view.addSampleButton.clicked.connect(lambda: self.add_sample())
        self._view.deleteSampleButton.clicked.connect(lambda: self.delete_sample())
        self._view.sortSamplesButton.clicked.connect(lambda: self.sort_samples())

        self._view.addCohortButton.clicked.connect(lambda: self.add_cohort())
        self._view.deleteCohortButton.clicked.connect(lambda: self.delete_cohort())
        self._view.tableView.horizontalHeader().editingFinished.connect(
            lambda col, name: self.update_cohort_name(col, name)
        )

    def add_sample(self):
        # update model
        row = len(self.samples)

        index = self._model.createIndex(row, 0)
        self._model.layoutAboutToBeChanged.emit()
        self._model.beginInsertRows(index, row, row)

        sample = Sample(name=f"New sample {row + 1}")
        self.samples.append(sample)

        self._model.endInsertRows()
        self._model.layoutChanged.emit()

        # update view
        self._view.tableView.setFocus()
        self._view.tableView.setCurrentIndex(index)

    def delete_sample(self):
        # update model
        indexes: List[QModelIndex] = self._view.tableView.selectedIndexes()
        index = indexes[0]  # selection model guarantees exactly one selection
        row = index.row()

        self._model.layoutAboutToBeChanged.emit()
        self._model.beginRemoveRows(index, row, row)

        del self.samples[row]

        self._model.endRemoveRows()
        self._model.layoutChanged.emit()

        # update selection
        if row >= len(self.samples):  # outside bounds
            self._view.tableView.clearSelection()
        else:
            self._view.tableView.setCurrentIndex(index)
            self._view.tableView.setFocus()

        self._view.updateButtons()

    def sort_samples(self):
        # update model
        natkey = natsort_keygen(key=sample_key)

        old_samples = copy.copy(self.samples)
        self.samples.sort(key=natkey)
        if self.samples != old_samples:
            self._model.layoutChanged.emit()

        # update view
        self._view.tableView.setFocus()

    def add_cohort(self):
        # update model
        cohort_names = get_cohort_names(self.samples)

        cohort_col = 1
        name = f"Cohort group {cohort_col}"
        while name in cohort_names:
            cohort_col += 1
            name = f"Cohort group {cohort_col}"

        col = self._model.columnCount()

        index = self._model.createIndex(0, col)
        self._model.layoutAboutToBeChanged.emit()
        self._model.beginInsertColumns(index, col, col)

        for sample in self.samples:
            sample.cohorts[name] = ""

        self._model.endInsertColumns()
        self._model.layoutChanged.emit()

        # update view
        viewCol = get_cohort_names(self.samples).index(name) + len(Sample.keys)
        viewIndex = self._model.createIndex(0, viewCol)
        self._view.tableView.setFocus()
        self._view.tableView.setCurrentIndex(viewIndex)
        self._view.updateButtons()

    def delete_cohort(self):
        indexes: List[QModelIndex] = self._view.tableView.selectedIndexes()
        index = indexes[0]
        col = index.column()

        cohort_names = get_cohort_names(self.samples)
        name = cohort_names[col - len(Sample.keys)]

        # update model
        self._model.layoutAboutToBeChanged.emit()
        self._model.beginRemoveColumns(index, col, col)

        for sample in self.samples:
            try:
                del sample.cohorts[name]
            except KeyError:
                pass

        self._model.endRemoveColumns()
        self._model.layoutChanged.emit()

        # update view
        self._view.tableView.setFocus()
        if col >= self._model.columnCount():  # outside bounds
            self._view.tableView.clearSelection()
        else:
            self._view.tableView.setCurrentIndex(index)
        self._view.updateButtons()

    def update_cohort_name(self, col: int, name: str):
        cohort_names = get_cohort_names(self.samples)
        old_name = cohort_names[col - len(Sample.keys)]

        if old_name == name:
            return

        if name in cohort_names[len(Sample.keys) :]:
            return

        # update model
        for sample in self.samples:
            cohort_value = sample.cohorts.get(old_name, None)
            try:
                del sample.cohorts[old_name]
            except KeyError:
                pass
            sample.cohorts[name] = cohort_value

        # update view
        self._view.tableView.setFocus()
        indexes: List[QModelIndex] = self._view.tableView.selectedIndexes()
        if len(indexes) > 0:
            index = indexes[0]
            self._view.tableView.setCurrentIndex(index)
        else:
            self._view.tableView.clearSelection()
        self._view.updateButtons()
