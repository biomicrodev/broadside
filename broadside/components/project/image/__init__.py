import logging
from pathlib import Path
from typing import List, Any, Tuple

from qtpy.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    Qt,
    Signal,
    QAbstractItemModel,
)
from qtpy.QtWidgets import (
    QTableView,
    QAbstractItemView,
    QHeaderView,
    QLayout,
    QLayoutItem,
    QWidget,
    QVBoxLayout,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QFileDialog,
    QDialog,
)
from natsort import natsort_keygen

from ...editor import Editor
from ...utils import ComboBoxDelegate, NamesModel
from ...viewermodel import ViewerModel
from ....models.block import Block
from ....models.image import Image
from ....models.panel import Panel


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


def getNames(items: List) -> List[str]:
    def key(name: str) -> Tuple[bool, str]:
        return name == "", name

    natkey = natsort_keygen(key=key)
    names = sorted([i.name for i in items], key=natkey)
    return names


class ImageTableModel(QAbstractTableModel):
    """
    TODO: be able to sort image table
    """

    keys = ["relpath", "block_name", "panel_name"]
    headers = ["Path", "Block", "Panel"]
    types = [Path, str, str]

    def __init__(self, basepath: Path, images: List[Image], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.basepath = basepath
        self.images = images

    def data(self, index: QModelIndex, role: Qt.ItemDataRole = None) -> Any:
        if role in [Qt.DisplayRole, Qt.EditRole, Qt.ToolTipRole]:
            row = index.row()
            col = index.column()

            key = self.keys[col]
            value = getattr(self.images[row], key)

            return str(value)

        elif role == Qt.TextAlignmentRole:
            col = index.column()
            key = self.keys[col]

            if key == "relpath":
                # see https://stackoverflow.com/a/35175211 for `int()`
                return int(Qt.AlignLeft | Qt.AlignVCenter)
            else:
                return Qt.AlignCenter

    def setData(
        self, index: QModelIndex, value: Any, role: Qt.ItemDataRole = None
    ) -> bool:
        if role == Qt.EditRole:
            row = index.row()
            col = index.column()

            key = self.keys[col]
            type_ = self.types[col]

            value = type_(value)
            oldValue = getattr(self.images[row], key)
            if oldValue == value:
                return False

            if key == "relpath":
                dstAbspath = value
                dstRelpath = dstAbspath.relative_to(self.basepath / Image.images_dir)

                # remove duplicates
                for image in self.images:
                    if dstRelpath == image.relpath:
                        return False

                # move image
                self.images[row].move(self.basepath, dstRelpath)
                self.dataChanged.emit(index, index, Qt.EditRole)
                return True

            else:
                setattr(self.images[row], key, value)
                self.dataChanged.emit(index, index, Qt.EditRole)
                return True

        return False

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        return super().flags(index) | Qt.ItemIsEditable

    def rowCount(self, parent: QModelIndex = None, *args, **kwargs) -> int:
        return len(self.images)

    def columnCount(self, parent: QModelIndex = None, *args, **kwargs) -> int:
        return len(self.keys)

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole = None
    ) -> Any:
        if role == Qt.DisplayRole:
            # column headers
            if orientation == Qt.Horizontal:
                return self.headers[section]

            # row headers
            elif orientation == Qt.Vertical:
                return section + 1


class FileRenameDelegate(QStyledItemDelegate):
    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ) -> QWidget:
        view: ImageTableView = option.widget
        model: ImageTableModel = view.model()
        path: str = model.data(index, Qt.EditRole)
        path = Path(path)
        abspath = model.basepath / Image.images_dir / path

        dialog = QFileDialog(parent.window(), Qt.Dialog)
        dialog.setWindowModality(Qt.ApplicationModal)
        dialog.setMinimumWidth(800)
        dialog.setMinimumHeight(600)
        dialog.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog)
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setViewMode(QFileDialog.Detail)
        dialog.setDirectory(str(abspath.parent))
        dialog.selectFile(str(abspath.name))
        dialog.setLabelText(QFileDialog.LookIn, "Rename image file")

        return dialog

    def setModelData(
        self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex
    ) -> None:
        editor: QFileDialog
        result: int = editor.result()
        if result == QDialog.Accepted:
            # if accepted, this means that the user also wanted to overwrite the file
            dstPath: str = editor.selectedFiles()[0]
            dstPath: Path = Path(dstPath)

            model.setData(index, dstPath, Qt.EditRole)


class ImageTableView(QTableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fileRenameDelegate = FileRenameDelegate(parent=self)
        self.setItemDelegateForColumn(0, self.fileRenameDelegate)

        self.blockComboBoxDelegate = ComboBoxDelegate(parent=self)
        self.setItemDelegateForColumn(1, self.blockComboBoxDelegate)

        self.panelComboBoxDelegate = ComboBoxDelegate(parent=self)
        self.setItemDelegateForColumn(2, self.panelComboBoxDelegate)

        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setWordWrap(False)

        horizontalHeader: QHeaderView = self.horizontalHeader()
        horizontalHeader.setStretchLastSection(True)


class ImageListEditorView(QWidget):
    imageListChanged = Signal()

    def __init__(
        self,
        basepath: Path,
        images: List[Image],
        blocks: List[Block],
        panels: List[Panel],
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)

        self.images = images
        self.blocks = blocks
        self.panels = panels

        self.model = ImageTableModel(basepath, images)
        self.view = ImageTableView()
        self.view.setModel(self.model)
        self.view.setColumnWidth(0, 300)

        # init UI
        layout = QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)

        # bindings
        self.model.dataChanged.connect(lambda _: self.imageListChanged.emit())

        # initialize
        blockNames = getNames(blocks)
        self.blockNamesModel = NamesModel(blockNames)
        self.view.blockComboBoxDelegate.setModel(self.blockNamesModel)

        panelNames = getNames(panels)
        self.panelNamesModel = NamesModel(panelNames)
        self.view.panelComboBoxDelegate.setModel(self.panelNamesModel)

    def refresh(self) -> None:
        blockNames = getNames(self.blocks)
        self.blockNamesModel.updateNames(blockNames)

        panelNames = getNames(self.panels)
        self.panelNamesModel.updateNames(panelNames)


class ImageListEditor(Editor):
    log = logging.getLogger(__name__)

    imageListChanged = Signal()

    def __init__(self, model: ViewerModel, *args, **kwargs):
        super().__init__(*args, **kwargs)

        basepath = model.path

        self.model = model
        self.view = ImageListEditorView(
            basepath,
            images=model.state.images,
            blocks=model.state.blocks,
            panels=model.state.panels,
        )

        # set up bindings
        self.view.imageListChanged.connect(lambda: self.imageListChanged.emit())
        self.imageListChanged.connect(lambda: self.validate())

        self.validate()

    def validate(self) -> None:
        """
        Nothing to validate, since we allow images with empty blocks and panels
        """
        self.isValid = True

    def refresh(self) -> None:
        self.view.refresh()
        self.validate()
