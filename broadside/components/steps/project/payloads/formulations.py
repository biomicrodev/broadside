import copy
import logging
from typing import Any, Tuple, List

from natsort import natsort_keygen
from qtpy.QtCore import QAbstractTableModel, QModelIndex, Qt, QItemSelectionModel
from qtpy.QtWidgets import (
    QTableView,
    QAbstractItemView,
    QHeaderView,
    QWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
)

from ....utils import CellState, LineEditItemDelegate
from .....models.payload import Formulation
from .....utils.events import EventedAngle, EventedList


class FormulationsTableModel(QAbstractTableModel):
    def __init__(self, formulations: EventedList[Formulation], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.formulations = formulations

    def data(self, index: QModelIndex, role: Qt.ItemDataRole = None) -> Any:
        if role in [Qt.DisplayRole, Qt.EditRole, Qt.ToolTipRole]:
            key = Formulation.keys[index.column()]
            value = getattr(self.formulations[index.row()], key)

            if value is None:
                return ""
            else:
                if key == "angle":
                    # for now, since we almost always work with clean divisors of 360
                    value: EventedAngle
                    value: int = value.int
                return str(value)

        elif role == Qt.BackgroundRole:
            row = index.row()
            key = Formulation.keys[index.column()]
            value = getattr(self.formulations[row], key)

            if (key in ["level", "name"]) and (value == ""):
                return CellState.Invalid

            # are formulations unique? (up to level, angle)
            levelAngle = (self.formulations[row].level, self.formulations[row].angle)
            otherLevelsAngles = [
                (f.level, f.angle) for i, f in enumerate(self.formulations) if i != row
            ]
            if levelAngle in otherLevelsAngles:
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

            key = Formulation.keys[col]
            type_ = Formulation.types[col]

            try:
                value = type_(value)
            except ValueError:
                return False

            if key == "angle":
                self.formulations[row].angle.deg = int(round(value))
            else:
                setattr(self.formulations[row], key, value)

            self.dataChanged.emit(index, index, [Qt.EditRole])
            return True

        return False

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        return super().flags(index) | Qt.ItemIsEditable

    def rowCount(self, parent: QModelIndex = None, *args, **kwargs) -> int:
        return len(self.formulations)

    def columnCount(self, parent: QModelIndex = None, *args, **kwargs) -> int:
        return len(Formulation.keys)

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole = None
    ) -> Any:
        if role == Qt.DisplayRole:
            # column headers
            if orientation == Qt.Horizontal:
                return Formulation.headers[section]

            # row headers
            elif orientation == Qt.Vertical:
                return section + 1  # section is 0-indexed


class FormulationsTableView(QTableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setSelectionMode(QAbstractItemView.SingleSelection)
        horizontalHeader: QHeaderView = self.horizontalHeader()
        horizontalHeader.setStretchLastSection(True)

        delegate = LineEditItemDelegate(parent=self)
        self.setItemDelegate(delegate)


class FormulationsEditorView(QWidget):
    def __init__(self, tableView: FormulationsTableView, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.tableView = tableView

        self.initUI()
        self.initBindings()

    def initUI(self):
        addFormulationButton = QPushButton()
        addFormulationButton.setText("Add formulation")
        addFormulationButton.setCursor(Qt.PointingHandCursor)
        self.addFormulationButton = addFormulationButton

        deleteFormulationButton = QPushButton()
        deleteFormulationButton.setText("Delete formulation")
        deleteFormulationButton.setObjectName("deleteFormulationButton")
        deleteFormulationButton.setDisabled(True)
        deleteFormulationButton.setCursor(Qt.ForbiddenCursor)
        self.deleteFormulationButton = deleteFormulationButton

        sortFormulationsButton = QPushButton()
        sortFormulationsButton.setText("Sort")
        sortFormulationsButton.setCursor(Qt.PointingHandCursor)
        self.sortFormulationsButton = sortFormulationsButton

        buttonsLayout = QHBoxLayout()
        buttonsLayout.addWidget(addFormulationButton)
        buttonsLayout.addWidget(deleteFormulationButton)
        buttonsLayout.addWidget(sortFormulationsButton)

        layout = QVBoxLayout()
        layout.addWidget(self.tableView, 1)
        layout.addLayout(buttonsLayout, 0)

        groupBox = QGroupBox()
        groupBox.setTitle("Formulations")
        groupBox.setLayout(layout)

        parentLayout = QVBoxLayout()
        parentLayout.addWidget(groupBox)
        self.setLayout(parentLayout)

    def initBindings(self):
        selectionModel: QItemSelectionModel = self.tableView.selectionModel()
        selectionModel.selectionChanged.connect(lambda: self.updateButtons())

    def updateButtons(self):
        indexes: List[int] = self.tableView.selectedIndexes()
        self.deleteFormulationButton.setEnabled(len(indexes) > 0)
        self.deleteFormulationButton.setCursor(
            Qt.PointingHandCursor if (len(indexes) > 0) else Qt.ForbiddenCursor
        )


def formulation_key(f: Formulation) -> Tuple[bool, str, float]:
    return (f.level == ""), f.level, f.angle.deg


class FormulationsEditor:
    log = logging.getLogger(__name__)

    def __init__(self, formulations: EventedList[Formulation]):
        self.formulations = formulations

        # set up Qt model/view
        self._model = FormulationsTableModel(formulations)
        table_view = FormulationsTableView()
        table_view.setModel(self._model)
        self._view = FormulationsEditorView(table_view)
        self._view.setMaximumWidth(600)
        self._view.setMinimumHeight(300)

        # bindings from view to model
        self._view.addFormulationButton.clicked.connect(lambda: self.add_formulation())
        self._view.deleteFormulationButton.clicked.connect(
            lambda: self.delete_formulation()
        )
        self._view.sortFormulationsButton.clicked.connect(
            lambda: self.sort_formulations()
        )

        # bindings from model to view
        self.formulations.events.changed.connect(lambda _: self._view.updateButtons())

    def add_formulation(self):
        # update model
        row = len(self.formulations)

        index = self._model.createIndex(row, 0)
        self._model.layoutAboutToBeChanged.emit()
        self._model.beginInsertRows(index, row, row)

        self.formulations.append(Formulation(name=f"Formulation {row + 1}"))

        self._model.endInsertRows()
        self._model.layoutChanged.emit()

        # update view
        self._view.tableView.setCurrentIndex(index)
        self._view.tableView.setFocus()

    def delete_formulation(self):
        indexes: List[QModelIndex] = self._view.tableView.selectedIndexes()
        index = indexes[0]  # selection model guarantees exactly one selection
        row = index.row()

        # update model
        self._model.layoutAboutToBeChanged.emit()
        self._model.beginRemoveRows(index, row, row)

        del self.formulations[row]

        self._model.endRemoveRows()
        self._model.layoutChanged.emit()

        # update view
        if row >= len(self.formulations):
            self._view.tableView.clearSelection()
        else:
            self._view.tableView.setCurrentIndex(index)
            self._view.tableView.setFocus()

    def sort_formulations(self):
        natkey = natsort_keygen(key=formulation_key)

        # copying like this is okay since this list won't ever be more than 40
        # formulations

        old_formulations = copy.copy(self.formulations)
        self.formulations.sort(key=natkey)
        if self.formulations != old_formulations:
            self._model.layoutChanged.emit()
