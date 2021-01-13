from typing import List, Any

from PySide2.QtCore import Qt, QAbstractTableModel, QModelIndex, QTimer, Signal
from PySide2.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QSplitter,
    QTableView,
    QAbstractItemView,
    QHeaderView,
    QProgressBar,
    QLabel,
    QApplication,
    QGroupBox,
)
from napari._qt.qt_viewer import QtViewer
from napari.components import ViewerModel as NapariViewerModel

from ..viewermodel import ViewerModel
from ...models.image import Image


class ImageTableModel(QAbstractTableModel):
    keys = ["relpath", "block_name", "panel_name"]
    headers = ["Path", "Block", "Panel"]

    def __init__(self, images: List[Image], *args, **kwargs):
        super().__init__(*args, **kwargs)

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


class ImageTableView(QTableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setWordWrap(False)

        horizontalHeader: QHeaderView = self.horizontalHeader()
        horizontalHeader.setStretchLastSection(True)


class AnnotationView(QWidget):
    isBusyChanged = Signal()

    def __init__(self, model: ViewerModel, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # TODO: refactor this logic out
        self._isBusy = False
        self.isBusy = True

        QApplication.setOverrideCursor(Qt.WaitCursor)

        self.imageTableModel = ImageTableModel(model.state.images)
        self.imageTableView = ImageTableView()
        self.imageTableView.setModel(self.imageTableModel)

        self.initUI()

    def initUI(self):
        progressBar = QProgressBar()
        progressBar.setMaximumHeight(40)
        progressBar.setMaximumWidth(250)
        progressBar.setMinimum(0)
        progressBar.setMaximum(0)
        progressLabel = QLabel()
        progressLabel.setText("Loading ...")
        progressLayout = QVBoxLayout()
        progressLayout.setAlignment(Qt.AlignCenter)
        progressLayout.addStretch(1)
        progressLayout.addWidget(progressBar)
        progressLayout.addWidget(progressLabel)
        progressLayout.addStretch(1)
        progressWidget = QWidget()
        progressWidget.setLayout(progressLayout)

        layout = QVBoxLayout()
        layout.addWidget(self.imageTableView)
        imageTableBox = QGroupBox()
        imageTableBox.setTitle("Images")
        imageTableBox.setLayout(layout)

        splitter = QSplitter()
        splitter.setHandleWidth(8)
        splitter.setObjectName("annotationSplitter")
        splitter.setOrientation(Qt.Horizontal)

        splitter.addWidget(imageTableBox)
        splitter.addWidget(progressWidget)

        splitter.setSizes([25, 75])
        self.splitter = splitter

        layout = QVBoxLayout()
        layout.addWidget(splitter)
        self.setLayout(layout)

        QTimer.singleShot(0, self.load)

    def load(self):
        self.napariViewerModel = NapariViewerModel()
        self.napariViewerModel.theme = "light"
        self.napariViewer = QtViewer(self.napariViewerModel)
        self.splitter.replaceWidget(1, self.napariViewer)
        self.isBusy = False

    @property
    def isBusy(self) -> bool:
        return self._isBusy

    @isBusy.setter
    def isBusy(self, val: bool) -> None:
        if self._isBusy is not val:
            self._isBusy = val
            self.isBusyChanged.emit()
