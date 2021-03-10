import logging
from pathlib import Path
from typing import List, Any, Tuple

from natsort import natsort_keygen
from qtpy.QtCore import QAbstractTableModel, QModelIndex, Qt, QAbstractItemModel
from qtpy.QtWidgets import (
    QTableView,
    QAbstractItemView,
    QHeaderView,
    QWidget,
    QVBoxLayout,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QFileDialog,
    QDialog,
    QScrollArea,
)

from ..blocks.devices import NamesDelegate
from ....editor import Editor
from ....viewer_model import ViewerModel
from .....models.block import Block
from .....models.image import Image
from .....models.panel import Panel


def get_names(items: List) -> List[str]:
    def key(name: str) -> Tuple[bool, str]:
        return name == "", name

    natkey = natsort_keygen(key=key)
    names = sorted([i.name for i in items], key=natkey)
    return names


class ImagesTableModel(QAbstractTableModel):
    keys = ["relpath", "block_name", "panel_name"]
    headers = ["Path", "Block", "Panel"]
    types = [Path, str, str]

    def __init__(self, basepath: Path, images: List[Image]):
        super().__init__()

        self.basepath = basepath
        self.images = images

    def data(self, index: QModelIndex, role: Qt.ItemDataRole = None):
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
    def initStyleOption(self, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        super().initStyleOption(option, index)
        option.textElideMode = Qt.ElideMiddle

    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ) -> QWidget:
        view: ImagesTableView = option.widget
        model: ImagesTableModel = view.model()
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


class ImagesTableView(QTableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setWordWrap(False)

        horizontalHeader: QHeaderView = self.horizontalHeader()
        horizontalHeader.setStretchLastSection(True)


class ImagesEditorView(QWidget):
    def __init__(self, tableView: ImagesTableView):
        super().__init__()

        scrollArea = QScrollArea()
        scrollArea.setWidget(tableView)
        scrollArea.setWidgetResizable(True)

        layout = QVBoxLayout()
        layout.addWidget(scrollArea)
        self.setLayout(layout)


class ImagesEditor(Editor):
    log = logging.getLogger(__name__)

    def __init__(self, model: ViewerModel):
        super().__init__()

        self.model = model
        blocks = model.state.blocks
        panels = model.state.panels

        # set up Qt models/views
        self.images_model = ImagesTableModel(model.path, model.state.images)

        table_view = ImagesTableView()
        table_view.setModel(self.images_model)
        table_view.setColumnWidth(0, 300)

        file_rename_delegate = FileRenameDelegate(parent=table_view)
        block_names_delegate = NamesDelegate(blocks)
        panel_names_delegate = NamesDelegate(panels)

        table_view.setItemDelegateForColumn(0, file_rename_delegate)
        table_view.setItemDelegateForColumn(1, block_names_delegate._view)
        table_view.setItemDelegateForColumn(2, panel_names_delegate._view)
        self._view = ImagesEditorView(table_view)

        blocks.events.deleted.connect(lambda _: self._validate_block_names())
        blocks.events.added.connect(lambda d: self._add_block_bindings(d["item"]))
        for block in blocks:
            self._add_block_bindings(block)

        panels.events.deleted.connect(lambda _: self._validate_panel_names())
        panels.events.added.connect(lambda d: self._add_panel_bindings(d["item"]))
        for panel in panels:
            self._add_panel_bindings(panel)

        self.validate()

    def _validate_block_names(self):
        block_names = [block.name for block in self.model.state.blocks]
        for image in self.model.state.images:
            if image.block_name not in block_names:
                image.block_name = ""

    def _validate_panel_names(self):
        panel_names = [panel.name for panel in self.model.state.panels]
        for image in self.model.state.images:
            if image.panel_name not in panel_names:
                image.panel_name = ""

    def _add_block_bindings(self, block: Block):
        def update(old_name: str, new_name: str):
            indexes_to_update = []
            for i, image in enumerate(self.model.state.images):
                if image.block_name == old_name:
                    image.block_name = new_name
                    indexes_to_update.append(i)

            col = ImagesTableModel.keys.index("block_name")
            for i in indexes_to_update:
                index = self.images_model.index(i, col)
                self.images_model.dataChanged.emit(index, index, [Qt.EditRole])

        block.events.name.connect(lambda d: update(d["old"], d["new"]))

    def _add_panel_bindings(self, panel: Panel):
        def update(old_name: str, new_name: str):
            indexes_to_update = []
            for i, image in enumerate(self.model.state.images):
                if image.panel_name == old_name:
                    image.panel_name = new_name
                    indexes_to_update.append(i)

            col = ImagesTableModel.keys.index("panel_name")
            for i in indexes_to_update:
                index = self.images_model.index(i, col)
                self.images_model.dataChanged.emit(index, index, [Qt.EditRole])

        panel.events.name.connect(lambda d: update(d["old"], d["new"]))

    def validate(self) -> None:
        invalid_image_indexes = self.model.state.invalid_image_indexes()
        self.is_valid = len(invalid_image_indexes) == 0
