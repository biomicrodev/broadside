import sys
from enum import Enum
from typing import Optional, List, Any

from PySide2.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    Qt,
    QRect,
    QItemSelectionModel,
)
from PySide2.QtGui import QPainter, QColor, QPen
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
    QApplication,
    QHeaderView,
)
from natsort import natsort_keygen

from broadside.gui.models.formulation import Formulation


class CellState(Enum):
    Valid = "VALID"
    Invalid = "INVALID"


class FormulationTableModel(QAbstractTableModel):
    def __init__(
        self, *args, formulations: Optional[List[Formulation]] = None, **kwargs
    ):
        super().__init__(*args, **kwargs)

        self.formulations: List[Formulation] = formulations or []

    def data(self, index: QModelIndex, role: Qt.ItemDataRole = None) -> Any:
        if role in [Qt.DisplayRole, Qt.EditRole, Qt.ToolTipRole]:
            key = Formulation.keys[index.column()]
            value = getattr(self.formulations[index.row()], key)

            if value is None:
                return ""
            else:
                return str(value)

        elif role == Qt.BackgroundRole:
            key = Formulation.keys[index.column()]
            value = getattr(self.formulations[index.row()], key)

            if value == "" or value is None:
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
        self.formulations.append(Formulation())
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


class StyledItemDelegate(QStyledItemDelegate):
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
            pen.setColor(QColor(200, 50, 50))
            pen.setWidth(1)

            painter.setPen(pen)
            painter.drawRect(QRect(x, y, w, h))


class PayloadTableView(QTableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setSelectionMode(QAbstractItemView.SingleSelection)
        horizontalHeader: QHeaderView = self.horizontalHeader()
        horizontalHeader.setStretchLastSection(True)

        delegate = StyledItemDelegate(parent=self)
        self.setItemDelegate(delegate)


class PayloadWidget(QWidget):
    def __init__(self, *args, formulation: List[Formulation] = None, **kwargs):
        super().__init__(*args, **kwargs)

        self.model = FormulationTableModel(formulations=formulation)

        self.view = PayloadTableView()
        self.view.setModel(self.model)

        addFormulationButton = QPushButton()
        addFormulationButton.setText("Add formulation")
        addFormulationButton.clicked.connect(lambda: self.model.addFormulation())
        self.addFormulationButton = addFormulationButton

        def selectionChanged():
            indexes = self.view.selectedIndexes()
            nRows = self.model.rowCount()
            indexes = [index for index in indexes if index.row() < nRows]
            self.deleteFormulationButton.setEnabled(len(indexes) > 0)

        def deleteFormulation():
            # after deleting row, need to re-set index
            index: QModelIndex = self.view.selectedIndexes()[0]
            row = index.row()
            column = index.column()

            self.model.removeFormulation(row)

            modelIndex = self.model.createIndex(row, column)
            self.view.setCurrentIndex(modelIndex)

        deleteFormulationButton = QPushButton()
        deleteFormulationButton.setText("Delete formulation")
        deleteFormulationButton.setObjectName("DeleteFormulationButton")
        deleteFormulationButton.setDisabled(True)
        deleteFormulationButton.setStyleSheet(
            """\
QPushButton#DeleteFormulationButton {
    background-color: rgb(190, 30, 30);
}
QPushButton#DeleteFormulationButton:enabled {
    color: white;
}
        """
        )
        deleteFormulationButton.clicked.connect(lambda: deleteFormulation())
        self.deleteFormulationButton = deleteFormulationButton

        selectionModel: QItemSelectionModel = self.view.selectionModel()
        selectionModel.selectionChanged.connect(lambda: selectionChanged())

        natsort = natsort_keygen(key=lambda a: (a.level, a.angle))

        def sort():
            self.model.formulations.sort(key=natsort)
            self.model.layoutChanged.emit()

        self.sortFormulationsButton = QPushButton()
        self.sortFormulationsButton.setText("Sort")
        self.sortFormulationsButton.clicked.connect(lambda: sort())

        buttonsLayout = QHBoxLayout()
        buttonsLayout.addWidget(self.addFormulationButton)
        buttonsLayout.addWidget(self.deleteFormulationButton)
        buttonsLayout.addWidget(self.sortFormulationsButton)

        layout = QVBoxLayout()
        layout.addWidget(self.view)
        layout.addLayout(buttonsLayout)

        self.setLayout(layout)


if __name__ == "__main__":
    app = QApplication()

    window = PayloadWidget()
    window.show()

    sys.exit(app.exec_())
