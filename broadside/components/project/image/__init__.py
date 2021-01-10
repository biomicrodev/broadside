import logging
from pathlib import Path
from typing import List, Any, Optional

from PySide2.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from PySide2.QtWidgets import (
    QTableView,
    QAbstractItemView,
    QHeaderView,
    QWidget,
    QVBoxLayout,
    QProgressBar,
    QLabel,
    QLayout,
    QLayoutItem,
)

from broadside.components.editor import Editor
from broadside.components.task import Report
from broadside.components.viewermodel import ViewerModel
from broadside.models.image import Image


def clearLayout(layout: QLayout) -> None:
    item: QLayoutItem = layout.takeAt(0)
    while item is not None:
        if item.widget() is not None:
            item.widget().deleteLater()
        elif item.layout() is not None:
            item.layout().deleteLater()

        layout.removeItem(item)
        item = layout.takeAt(0)


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
            col = index.column()
            key = self.keys[col]

            if key == "filepath":
                return Qt.AlignLeft | Qt.AlignVCenter
            else:
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
        self.setWordWrap(False)

        horizontalHeader: QHeaderView = self.horizontalHeader()
        horizontalHeader.setStretchLastSection(True)
        # horizontalHeader.setSectionResizeMode(QHeaderView.Stretch)


class ImageListEditorView(QWidget):
    def refresh(self):
        pass


class ImageListEditor(Editor):
    log = logging.getLogger(__name__)

    imageListChanged = Signal()

    def __init__(self, model: ViewerModel, *args, **kwargs):
        super().__init__(*args, **kwargs)

        basepath = model.path / model.state.images_dir
        self.tableModel = ImageTableModel(basepath, model.state.images)
        self.tableModel.dataChanged.connect(lambda _: self.imageListChanged.emit())
        # but not layoutChanged, since the layout won't change this way

        self._progressBar: Optional[QProgressBar] = None
        self._progressIndicator: Optional[QLabel] = None

        # set up view
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        self.view = ImageListEditorView()
        self.view.setLayout(layout)

        # init executor bindings
        if not model._images_loaded:
            model.executors["read-images"].register(
                started=self.startedLoadingImages,
                finished=self.finishedLoadingImages,
                progress=self.onProgress,
            )
        else:
            self.loadImageTable()

    def startedLoadingImages(self):
        self._progressBar = QProgressBar()
        self._progressBar.setOrientation(Qt.Horizontal)
        self._progressBar.setMinimumWidth(100)
        self._progressBar.setMaximumWidth(300)

        self._progressIndicator = QLabel()
        self._progressIndicator.setText("Loading images ...")

        layout = self.view.layout()
        clearLayout(layout)

        layout.setAlignment(Qt.AlignCenter)
        layout.addStretch(1)
        layout.addWidget(self._progressBar)
        layout.addWidget(self._progressIndicator)
        layout.addStretch(1)

    def onProgress(self, report: Report) -> None:
        self._progressBar.setMinimum(0)
        self._progressBar.setMaximum(report.total)
        self._progressBar.setValue(report.iter)

        self._progressIndicator.setText(f"Loading image {report.iter}/{report.total}")

    def finishedLoadingImages(self):
        self.log.info("Finished loading images")
        self.loadImageTable()

    def validate(self) -> None:
        self.isValid = True  # TODO: replace with actual image list validation logic

    def loadImageTable(self):
        layout: QLayout = self.view.layout()
        clearLayout(layout)

        tableView = ImageTableView()
        tableView.setModel(self.tableModel)
        layout.addWidget(tableView, 1)

        self.validate()
