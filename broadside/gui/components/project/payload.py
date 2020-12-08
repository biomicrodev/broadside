import logging
from typing import List, Any

from PySide2.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    Qt,
    QRect,
    QItemSelectionModel,
    Signal,
)
from PySide2.QtGui import QPainter, QPen
from PySide2.QtWidgets import (
    QWidget,
    QTableView,
    QAbstractItemView,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QHeaderView,
)
from natsort import natsort_keygen

from broadside.gui.color import Color
from broadside.gui.components import CellState
from broadside.gui.models.formulation import Formulation


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
            key = Formulation.keys[index.column()]
            value = getattr(self.formulations[index.row()], key)

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

            key = Formulation.keys[index.column()]
            type_ = Formulation.types[index.column()]
            try:
                setattr(self.formulations[index.row()], key, type_(value))
                self.dataChanged.emit(QModelIndex(), QModelIndex(), Qt.EditRole)
            except ValueError:
                return False

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

    def addFormulation(self):
        self.layoutAboutToBeChanged.emit()

        index = self.rowCount()
        self.beginInsertRows(QModelIndex(), index, index)
        self.formulations.append(Formulation.from_dict({}))
        self.endInsertRows()

        # self.changePersistentIndex(QModelIndex(), QModelIndex())
        self.layoutChanged.emit()

    def removeFormulation(self, index):
        self.layoutAboutToBeChanged.emit()

        self.beginRemoveRows(QModelIndex(), index, index)
        del self.formulations[index]
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


class FormulationTableView(QTableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setSelectionMode(QAbstractItemView.SingleSelection)
        horizontalHeader: QHeaderView = self.horizontalHeader()
        horizontalHeader.setStretchLastSection(True)

        delegate = LineEditItemDelegate(parent=self)
        self.setItemDelegate(delegate)


class FormulationTableEditorView(QWidget):
    log = logging.getLogger(__name__)

    dataChanged = Signal()

    def __init__(self, formulations: List[Formulation], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.model = FormulationTableModel(formulations=formulations)
        self.model.dataChanged.connect(lambda _: self.dataChanged.emit())
        self.model.layoutChanged.connect(lambda: self.dataChanged.emit())

        self.view = FormulationTableView()
        self.view.setModel(self.model)

        def addFormulation():
            self.model.addFormulation()

            row = self.model.rowCount() - 1
            column = 0
            modelIndex = self.model.createIndex(row, column)
            self.view.setCurrentIndex(modelIndex)
            self.view.setFocus()

        addFormulationButton = QPushButton()
        addFormulationButton.setText("Add formulation")
        addFormulationButton.clicked.connect(lambda: addFormulation())
        self.addFormulationButton = addFormulationButton

        def deleteFormulation():
            # after deleting row, need to re-set index
            index: QModelIndex = self.view.selectedIndexes()[0]
            row = index.row()
            column = index.column()

            self.model.removeFormulation(row)

            modelIndex = self.model.createIndex(row, column)
            self.view.setCurrentIndex(modelIndex)
            self.view.setFocus()

        deleteFormulationButton = QPushButton()
        deleteFormulationButton.setText("Delete formulation")
        deleteFormulationButton.setObjectName("deleteFormulationButton")
        deleteFormulationButton.setDisabled(True)
        deleteFormulationButton.clicked.connect(lambda: deleteFormulation())
        self.deleteFormulationButton = deleteFormulationButton

        def selectionChanged():
            indexes = self.view.selectedIndexes()
            nRows = self.model.rowCount()
            indexes = [index for index in indexes if index.row() < nRows]
            self.deleteFormulationButton.setEnabled(len(indexes) > 0)

        selectionModel: QItemSelectionModel = self.view.selectionModel()
        selectionModel.selectionChanged.connect(lambda: selectionChanged())

        natsort = natsort_keygen(
            key=lambda a: (a.level is None, a.angle is None, a.level, a.angle)
        )

        def sort():
            self.model.formulations.sort(key=natsort)
            self.model.layoutChanged.emit()

        sortFormulationsButton = QPushButton()
        sortFormulationsButton.setText("Sort")
        sortFormulationsButton.clicked.connect(lambda: sort())
        self.sortFormulationsButton = sortFormulationsButton

        buttonsLayout = QHBoxLayout()
        buttonsLayout.addWidget(self.addFormulationButton)
        buttonsLayout.addWidget(self.deleteFormulationButton)
        buttonsLayout.addWidget(self.sortFormulationsButton)

        layout = QVBoxLayout()
        layout.addWidget(self.view)
        layout.addLayout(buttonsLayout)

        self.setLayout(layout)
