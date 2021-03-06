from enum import Enum, auto
from pathlib import Path
from typing import Optional, List, Any

from qtpy.QtCore import Qt, QDir, Signal, QRect, QSize, QModelIndex, QAbstractListModel
from qtpy.QtGui import (
    QFontMetrics,
    QMouseEvent,
    QResizeEvent,
    QIcon,
    QPainter,
    QPen,
    QColor,
)
from qtpy.QtWidgets import (
    QFrame,
    QLabel,
    QMessageBox,
    QWidget,
    QFileDialog,
    QTabBar,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QComboBox,
    QLayoutItem,
    QLayout,
)

from ..utils.colors import Color
from ..utils.events import EventedList


class CellState(Enum):
    Valid = auto()
    Invalid = auto()


class QHLine(QFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setFixedHeight(1)
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Plain)


class QElidedLabel(QLabel):
    def setText(self, text: str) -> None:
        metrics = QFontMetrics(self.font())
        elidedText: str = metrics.elidedText(text, Qt.ElideMiddle, self.width())
        super().setText(elidedText)


class EditableTabBar(QTabBar):
    tabDoubleClicked = Signal(int)
    editingFinished = Signal(int)
    tabLayoutChanged = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTabsClosable(True)
        self.setMovable(True)
        self.setCursor(Qt.ArrowCursor)

    def tabLayoutChange(self):
        super().tabLayoutChange()
        self.tabLayoutChanged.emit()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.NoButton:
            self.setCursor(Qt.ClosedHandCursor)
        super().mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        tabIndex = self.tabAt(event.pos())
        self.tabDoubleClicked.emit(tabIndex)
        self.startEdit(tabIndex)

    def startEdit(self, tabIndex: int) -> None:
        self.editingTabIndex = tabIndex
        rect: QRect = self.tabRect(tabIndex)

        topMargin = 3
        leftMargin = 6

        lineEdit = QLineEdit(self)
        lineEdit.setAlignment(Qt.AlignCenter)
        lineEdit.move(rect.left() + leftMargin, rect.top() + topMargin)
        lineEdit.resize(rect.width() - 2 * leftMargin, rect.height() - 2 * topMargin)
        lineEdit.setText(self.tabText(tabIndex))
        lineEdit.selectAll()
        lineEdit.setFocus()
        lineEdit.show()
        lineEdit.editingFinished.connect(self.finishEdit)
        self.lineEdit = lineEdit

    def finishEdit(self) -> None:
        self.setTabText(self.editingTabIndex, self.lineEdit.text())
        self.lineEdit.deleteLater()
        self.editingFinished.emit(self.editingTabIndex)


class EditableTabWidget(QTabWidget):
    buttonSize = 25
    scrollWidth = 44  # hard-copied from qss file

    tabMoved = Signal(int, int)
    editingFinished = Signal(int)

    def __init__(self, addButtonText: str = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.addButtonText = addButtonText

        tabBar = EditableTabBar()
        tabBar.tabLayoutChanged.connect(self.updateAddButtonPos)
        tabBar.tabMoved.connect(self.tabMoved)
        tabBar.editingFinished.connect(self.editingFinished)

        self.setTabBar(tabBar)
        self.initAddButton()

    def initAddButton(self):
        addTabButton = QPushButton()
        addTabButton.setParent(self)
        addTabButton.setIconSize(QSize(22, 22))
        addTabButton.setObjectName("addTabButton")
        addTabButton.setCursor(Qt.PointingHandCursor)
        self.addTabButton = addTabButton

        self.updateAddButtonPos()

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.updateAddButtonPos()

    def updateAddButtonPos(self):
        count = self.count()
        if count >= 1:
            addIcon = QIcon()
            addIcon.addFile("broadside/resources/icons/add.svg")
            self.addTabButton.setIcon(addIcon)
            self.addTabButton.setText(None)
            self.addTabButton.setFixedSize(self.buttonSize, self.buttonSize)
        else:
            self.addTabButton.setIcon(QIcon())
            self.addTabButton.setText(self.addButtonText)
            self.addTabButton.setFixedSize(
                self.addTabButton.sizeHint().width() + 10, self.buttonSize
            )

        heightOffset = 3 if count > 1 else 2

        totalTabWidth = sum(
            [self.tabBar().tabRect(i).width() for i in range(self.count())]
        )
        visibleWidth = self.width()
        if visibleWidth > totalTabWidth + self.buttonSize + 3:
            # add button is placed after all the tabs
            self.addTabButton.move(totalTabWidth + 2, heightOffset)

        elif (visibleWidth <= totalTabWidth + self.buttonSize + 3) and (
            visibleWidth >= totalTabWidth
        ):
            # move add button along with right edge of visible area
            self.addTabButton.move(visibleWidth - self.buttonSize, heightOffset)

        elif visibleWidth < totalTabWidth:
            # move add button to the left of the scroller buttons
            self.addTabButton.move(
                visibleWidth - self.buttonSize - self.scrollWidth + 1, heightOffset
            )


class LineEditItemDelegate(QStyledItemDelegate):
    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ) -> QWidget:
        editor = QLineEdit(parent=parent)
        editor.setAlignment(Qt.AlignCenter)
        editor.selectAll()
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
            pen.setColor(QColor(*(Color.Red).value))
            pen.setWidth(1)

            painter.setPen(pen)
            painter.drawRect(QRect(x, y, w, h))


class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.model: Optional[QAbstractListModel] = None

    def setModel(self, model: QAbstractListModel) -> None:
        self.model = model

    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ) -> QWidget:
        editor = QComboBox(parent=parent)

        if self.model is not None:
            editor.setModel(self.model)

        return editor


class NamesModel(QAbstractListModel):
    def __init__(self, names: List[str], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.names = names

    def data(self, index: QModelIndex, role: Qt.ItemDataRole = None) -> Any:
        if role in [Qt.DisplayRole, Qt.EditRole, Qt.ToolTipRole]:
            row = index.row()
            return self.names[row]

        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter

    def rowCount(self, parent: QModelIndex = None, *args, **kwargs):
        return len(self.names)


class NamesDelegate:
    def __init__(self, items: EventedList):
        self.items = items
        self.names = [item.name for item in items]

        # set up Qt model/view for names
        self._model = NamesModel(self.names)

        self._view = ComboBoxDelegate()
        self._view.setModel(self._model)

        # set up bindings
        items.events.added.connect(lambda d: self.add_name(d["item"].name))
        items.events.deleted.connect(lambda i: self.delete_name(i))
        items.events.swapped.connect(lambda d: self.swap_names(d["ind1"], d["ind2"]))

        items.events.added.connect(lambda d: self._add_item_bindings(d["item"]))
        for item in items:
            self._add_item_bindings(item)

    def add_name(self, name: str):
        self._model.layoutAboutToBeChanged.emit()
        self.names.append(name)
        self._model.layoutChanged.emit()

    def delete_name(self, row: int):
        # update model
        self._model.layoutAboutToBeChanged.emit()
        del self.names[row]
        self._model.layoutChanged.emit()

    def swap_names(self, to_: int, from_: int):
        (self.names[to_], self.names[from_]) = (self.names[from_], self.names[to_])

        to_index = self._model.index(to_, 0)
        from_index = self._model.index(from_, 0)
        self._model.dataChanged.emit(to_index, to_index, [Qt.EditRole])
        self._model.dataChanged.emit(from_index, from_index, [Qt.EditRole])

    def _add_item_bindings(self, item):
        item.events.name.connect(lambda name: self.update_name(item, name))

    def update_name(self, item, name: str):
        row = self.items.index(item)

        index = self._model.index(row, 0)
        self.names[row] = name
        self._model.dataChanged.emit(index, index, [Qt.EditRole])


def showSaveDialog(
    parent: QWidget = None, *, title: str, text: str
) -> QMessageBox.StandardButton:
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(text)
    box.setWindowModality(Qt.ApplicationModal)
    box.setIcon(QMessageBox.Question)
    box.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
    box.setDefaultButton(QMessageBox.Cancel)
    return box.exec_()


def showYesNoDialog(
    parent: QWidget = None, *, title: str, text: str
) -> QMessageBox.StandardButton:
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(text)
    box.setWindowModality(Qt.ApplicationModal)
    box.setIcon(QMessageBox.Question)
    box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    box.setDefaultButton(QMessageBox.No)
    return box.exec_()


def showSelectProjectDialog(parent: QWidget = None) -> Optional[Path]:
    dialog = QFileDialog(parent, Qt.Dialog)
    dialog.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog)
    dialog.setAcceptMode(QFileDialog.AcceptSave)
    dialog.setLabelText(QFileDialog.LookIn, "Select project folder")
    dialog.setFileMode(QFileDialog.Directory)
    dialog.setOption(QFileDialog.ShowDirsOnly, True)
    dialog.setViewMode(QFileDialog.Detail)
    dialog.setDirectory(QDir.homePath())

    if dialog.exec_():
        paths = dialog.selectedFiles()
        assert len(paths) == 1
        path = Path(paths[0])
        return path


def clearLayout(layout: QLayout) -> None:
    if layout.count() == 0:
        return

    item: QLayoutItem = layout.takeAt(0)
    while item is not None:
        if item.widget() is not None:
            item.widget().deleteLater()
        elif item.layout() is not None:
            item.layout().deleteLater()

        item = layout.takeAt(0)
