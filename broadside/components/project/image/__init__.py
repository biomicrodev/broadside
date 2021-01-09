import logging
from pathlib import Path
from typing import List, Any

from PySide2.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from PySide2.QtWidgets import (
    QTableView,
    QAbstractItemView,
    QHeaderView,
    QWidget,
    QVBoxLayout,
)

from broadside.components.editor import Editor
from broadside.components.viewermodel import ViewerModel
from broadside.models.image import Image


class ImageTableModel(QAbstractTableModel):
    keys = ["filepath", "block_name", "panel_name"]
    headers = ["Path", "Block", "Panel"]

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

            if key == "filepath":
                value: Path
                value = value.relative_to(self.basepath)

            return str(value)

        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter

    def rowCount(self, parent=None, *args, **kwargs) -> int:
        return len(self.images)

    def columnCount(self, parent=None, *args, **kwargs) -> int:
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


class ImageTableView(QTableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setSelectionMode(QAbstractItemView.SingleSelection)
        horizontalHeader: QHeaderView = self.horizontalHeader()
        horizontalHeader.setStretchLastSection(True)


class ImageListEditorView(QWidget):
    def refresh(self):
        pass


class ImageListEditor(Editor):
    log = logging.getLogger(__name__)

    imageListChanged = Signal()

    def __init__(self, model: ViewerModel, *args, **kwargs):
        super().__init__(*args, **kwargs)

        basepath = model.path / model.state.images_dir
        self.model = ImageTableModel(basepath, model.state.images)
        self.model.dataChanged.connect(lambda _: self.imageListChanged.emit())

        view = ImageTableView()
        view.setModel(self.model)

        layout = QVBoxLayout()
        layout.addWidget(view, 1)

        self.view = ImageListEditorView()
        self.view.setLayout(layout)

    def validate(self) -> None:
        self.isValid = True
