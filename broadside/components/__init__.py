from enum import Enum, auto

from PySide2.QtCore import QModelIndex, Qt, QRect
from PySide2.QtGui import QPainter, QPen
from PySide2.QtWidgets import (
    QStyledItemDelegate,
    QWidget,
    QStyleOptionViewItem,
    QLineEdit,
)

from .color import Color


class CellState(Enum):
    Valid = auto()
    Invalid = auto()


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
