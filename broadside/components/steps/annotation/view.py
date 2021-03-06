from typing import List, Any

from napari._qt.qt_viewer import QtViewer
from napari.components import ViewerModel as NapariViewerModel
from qtpy.QtCore import Qt, QAbstractTableModel, QModelIndex, Signal
from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QSplitter,
    QTableView,
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QGroupBox,
)

from ..project.block import BlockDiagramEditorView
from ...viewer_model import ViewerModel
from ....models.image import Image


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
        # self.isBusy = True

        self.model = model
        self.imageTableModel = ImageTableModel(model.state.images)
        self.imageTableView = ImageTableView()
        self.imageTableView.setModel(self.imageTableModel)
        self.imageTableView.setColumnWidth(0, 300)

        self.initUI()
        self.initBindings()

    def initUI(self) -> None:
        noImageSetLabel = QLabel()
        noImageSetLabel.setObjectName("noImageSetLabel")
        noImageSetLabel.setAlignment(Qt.AlignCenter)
        noImageSetLabel.setText("No image selected")

        imageTableViewLayout = QVBoxLayout()
        imageTableViewLayout.addWidget(self.imageTableView)
        imageTableBox = QGroupBox()
        imageTableBox.setTitle("Images")
        imageTableBox.setLayout(imageTableViewLayout)

        imageTableSplitter = QSplitter()
        imageTableSplitter.setHandleWidth(12)
        imageTableSplitter.setOrientation(Qt.Vertical)
        imageTableSplitter.addWidget(imageTableBox)
        imageTableSplitter.setSizes([500, 500])
        self.imageTableSplitter = imageTableSplitter

        splitter = QSplitter()
        splitter.setHandleWidth(12)
        splitter.setObjectName("annotationSplitter")
        splitter.setOrientation(Qt.Horizontal)
        splitter.addWidget(imageTableSplitter)
        splitter.addWidget(noImageSetLabel)
        splitter.setSizes([200, 300])
        self.splitter = splitter

        layout = QVBoxLayout()
        layout.addWidget(splitter)
        self.setLayout(layout)

    def initBindings(self) -> None:
        self.imageTableView.doubleClicked.connect(self.loadImage)

    def loadImage(self, index: QModelIndex) -> None:
        index = index.row()
        self.isBusy = True

        viewerWidget = self.splitter.widget(1)
        if isinstance(viewerWidget, QLabel):
            adjustWidget = self._createAdjustWidget(3)

            # need to load napari viewer here
            viewerModel = self.napariViewerModel = NapariViewerModel()
            viewerModel.theme = "light"

            napariViewer = QtViewer(viewerModel)
            napariViewer.setWindowFlags(Qt.Widget)
            self.napariViewer = napariViewer

            # create image viewer here
            imageViewer = QSplitter()
            imageViewer.setOrientation(Qt.Horizontal)
            imageViewer.setHandleWidth(12)
            imageViewer.addWidget(adjustWidget)
            imageViewer.addWidget(napariViewer)
            self.imageViewer = imageViewer

            self.splitter.replaceWidget(1, imageViewer)
            self.splitter.setSizes([200, 300])

        image: Image = self.model.state.images[index]

        # set up block diagram editor
        blockName = image.block_name
        block = next(
            (block for block in self.model.state.blocks if block.name == blockName),
            None,
        )
        if block is None:
            return
        blockDiagramEditorView = BlockDiagramEditorView(block, self.model.state.devices)
        blockDiagramEditorView.diagramWidget.setEnabled(False)
        if self.imageTableSplitter.count() == 1:
            self.imageTableSplitter.addWidget(blockDiagramEditorView)
        else:
            self.imageTableSplitter.replaceWidget(1, blockDiagramEditorView)
        self.imageTableSplitter.setSizes([200, 300])

        # remove all layers; can't do directly
        layers = self.napariViewerModel.layers
        layers.select_all()
        layers.remove_selected()

        # unset all other images; TODO: does this actually help with memory usage?
        for im in self.model.state.images:
            im.pixels = None

        image.load(self.model.path)

        # add image
        name = image.relpath.name
        pixels = image.pixels
        pyramids = pixels.pyramids + ([pixels.background] if pixels.background else [])
        for pyramid in pyramids:
            scale = pyramid.mpp
            scale = (scale.y, scale.x)

            translate = pyramid.offset
            translate = (translate.y, translate.x)

            if pixels.file_format == "scn" and pixels.axes != "YXS":
                scale = (1,) + scale
                translate = (0,) + translate

            self.napariViewerModel.add_image(
                data=pyramid.layers, name=name, scale=scale, translate=translate
            )

        self.isBusy = False

    @property
    def isBusy(self) -> bool:
        return self._isBusy

    @isBusy.setter
    def isBusy(self, val: bool) -> None:
        if self._isBusy is not val:
            self._isBusy = val
            self.isBusyChanged.emit()

    def _createAdjustWidget(self, channels: int) -> QWidget:
        label = QLabel("sliders go here")

        adjustLayout = QVBoxLayout()
        adjustLayout.addWidget(label)

        adjustWidget = QWidget()
        adjustWidget.setLayout(adjustLayout)

        return adjustWidget


class AnnotationView2(QWidget):
    isBusyChanged = Signal()

    @property
    def isBusy(self) -> bool:
        return self._isBusy

    @isBusy.setter
    def isBusy(self, val: bool) -> None:
        if self._isBusy is not val:
            self._isBusy = val
            self.isBusyChanged.emit()

    def __init__(self, model: ViewerModel, *args, **kwargs):
        super().__init__(*args, **kwargs)
