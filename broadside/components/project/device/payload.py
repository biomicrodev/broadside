import copy
import logging
from typing import List, Any, Type, Tuple

from PySide2.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    Qt,
    QItemSelectionModel,
    Signal,
    QAbstractItemModel,
)
from PySide2.QtWidgets import (
    QWidget,
    QTableView,
    QAbstractItemView,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QHeaderView,
)
from natsort import natsort_keygen

from ...utils import CellState, LineEditItemDelegate
from ....models.formulation import Formulation


class FormulationTableModel(QAbstractTableModel):
    def __init__(self, formulations: List[Formulation], *args, **kwargs):
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
                    value = int(value)
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
            column = index.column()

            key = Formulation.keys[column]
            type_ = Formulation.types[column]

            value = type_(value)
            oldValue = getattr(self.formulations[row], key)
            if oldValue == value:
                return False

            setattr(self.formulations[row], key, value)
            self.dataChanged.emit(QModelIndex(), QModelIndex(), Qt.EditRole)
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

    def addFormulation(self) -> None:
        self.layoutAboutToBeChanged.emit()

        index = self.rowCount()
        self.beginInsertRows(QModelIndex(), index, index)
        self.formulations.append(Formulation.from_dict({}))
        self.endInsertRows()

        self.layoutChanged.emit()

    def deleteFormulation(self, index: int) -> None:
        self.layoutAboutToBeChanged.emit()

        self.beginRemoveRows(QModelIndex(), index, index)
        del self.formulations[index]
        self.endRemoveRows()

        self.layoutChanged.emit()

    def sortFormulations(self) -> None:
        def key(f: Formulation) -> Tuple[bool, str, float]:
            return f.level == "", f.level, f.angle

        natkey = natsort_keygen(key=key)

        # copying like this is okay since this list won't ever be more than 40
        # formulations
        oldFormulations = copy.copy(self.formulations)
        self.formulations.sort(key=natkey)
        if self.formulations != oldFormulations:
            self.layoutChanged.emit()


class FormulationTableView(QTableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setSelectionMode(QAbstractItemView.SingleSelection)
        horizontalHeader: QHeaderView = self.horizontalHeader()
        horizontalHeader.setStretchLastSection(True)

        delegate = LineEditItemDelegate(parent=self)
        self.setItemDelegate(delegate)

    def formulationAdded(self) -> None:
        # only for setting current index
        model: Type[QAbstractItemModel] = self.model()

        row = model.rowCount() - 1
        column = 0
        modelIndex: QModelIndex = model.createIndex(row, column)
        self.setCurrentIndex(modelIndex)
        self.setFocus()

    def formulationDeleted(self, index: QModelIndex) -> None:
        # only for setting current index
        model: Type[QAbstractItemModel] = self.model()
        nRows = model.rowCount()
        row = index.row()
        column = index.column()

        if row != nRows:  # row is already deleted; subtle
            modelIndex = model.createIndex(row, column)
            self.setCurrentIndex(modelIndex)
            self.setFocus()


class FormulationTableEditorView(QWidget):
    log = logging.getLogger(__name__)

    formulationListChanged = Signal()

    def __init__(self, formulations: List[Formulation], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.model = FormulationTableModel(formulations)
        self.model.dataChanged.connect(lambda _: self.formulationListChanged.emit())
        self.model.layoutChanged.connect(lambda: self.formulationListChanged.emit())

        self.view = FormulationTableView()
        self.view.setModel(self.model)

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
        layout.addWidget(self.view, 1)
        layout.addLayout(buttonsLayout, 0)

        self.setLayout(layout)

    def initBindings(self):
        def addFormulation():
            self.model.addFormulation()
            self.view.formulationAdded()

        self.addFormulationButton.clicked.connect(lambda: addFormulation())

        def deleteFormulation():
            index: QModelIndex = self.view.selectedIndexes()[0]
            row = index.row()

            self.model.deleteFormulation(row)
            self.view.formulationDeleted(index)
            self.updateButtons()

        self.deleteFormulationButton.clicked.connect(lambda: deleteFormulation())

        self.sortFormulationsButton.clicked.connect(
            lambda: self.model.sortFormulations()
        )

        selectionModel: QItemSelectionModel = self.view.selectionModel()
        selectionModel.selectionChanged.connect(lambda: self.updateButtons())
        self.updateButtons()

    def updateButtons(self):
        indexes: List[int] = self.view.selectedIndexes()
        self.deleteFormulationButton.setEnabled(len(indexes) > 0)
        self.deleteFormulationButton.setCursor(
            Qt.PointingHandCursor if (len(indexes) > 0) else Qt.ForbiddenCursor
        )
