from enum import Enum, auto
from pathlib import Path
from typing import Optional

from PySide2.QtCore import Qt, QDir, Signal, QRect, QSize, QModelIndex
from PySide2.QtGui import QFontMetrics, QMouseEvent, QResizeEvent, QIcon, QPainter, QPen
from PySide2.QtWidgets import (
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
)

from .color import Color


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
        self.setCursor(Qt.OpenHandCursor)

    def tabLayoutChange(self):
        super().tabLayoutChange()
        self.tabLayoutChanged.emit()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        super().mousePressEvent(event)
        self.setCursor(Qt.ClosedHandCursor)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.setCursor(Qt.OpenHandCursor)
        super().mouseReleaseEvent(event)

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
            addIcon.addFile("broadside/resources/icons/add-24px.svg")
            self.addTabButton.setIcon(addIcon)
            self.addTabButton.setText(None)
            self.addTabButton.setFixedSize(self.buttonSize, self.buttonSize)
        else:
            self.addTabButton.setIcon(QIcon())
            self.addTabButton.setText(self.addButtonText)
            self.addTabButton.setFixedSize(
                self.addTabButton.sizeHint().width() + 10, self.buttonSize
            )

        totalTabWidth = sum(
            [self.tabBar().tabRect(i).width() for i in range(self.count())]
        )
        visibleWidth = self.width()
        if visibleWidth > totalTabWidth + self.buttonSize + 3:
            # add button is placed after all the tabs
            self.addTabButton.move(totalTabWidth + 1, 4)

        elif (visibleWidth <= totalTabWidth + self.buttonSize + 3) and (
            visibleWidth >= totalTabWidth
        ):
            # move add button along with right edge of visible area
            self.addTabButton.move(visibleWidth - self.buttonSize, 4)

        elif visibleWidth < totalTabWidth:
            # move add button to the left of the scroller buttons
            self.addTabButton.move(
                visibleWidth - self.buttonSize - self.scrollWidth + 1, 4
            )


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


def updateStyle(w: QWidget) -> None:
    w.style().unpolish(w)
    w.style().polish(w)
