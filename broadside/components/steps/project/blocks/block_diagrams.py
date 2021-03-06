from typing import List, Optional

from natsort import natsorted
from qtpy.QtCore import Signal, Qt, QPointF, QSize, QRectF
from qtpy.QtGui import (
    QBrush,
    QPainter,
    QResizeEvent,
    QColor,
    QWheelEvent,
    QTransform,
)
from qtpy.QtWidgets import (
    QSlider,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QGraphicsView,
    QGroupBox,
    QWidget,
    QGraphicsScene,
)

from .indicators import Indicator
from ....utils import clearLayout
from .....models.block import Block, Vector, Device
from .....models.payload import Payload
from .....utils.events import EventedList, EventedPoint


def get_levels(block: Block, payloads: EventedList[Payload]) -> List[str]:
    payload_names = set(d.payload_name for d in block.devices)

    levels = set()

    for payload in payloads:
        if payload.name in payload_names:
            levels.update([f.level for f in payload.formulations])
    levels = natsorted(list(levels))
    return levels


class Slider(QSlider):
    def __init__(self):
        super().__init__()

        self.setSingleStep(1)
        self.setTickInterval(1)
        self.setPageStep(1)
        self.setOrientation(Qt.Vertical)
        self.setTickPosition(QSlider.TicksLeft)
        self.setInvertedControls(True)
        self.setInvertedAppearance(True)


class VLabeledSlider(QWidget):
    valueChanged = Signal(str)

    def __init__(self):
        super().__init__()

        self.labels: Optional[List[str]] = None
        self.slider = Slider()

        self.labelsLayout = QVBoxLayout()

        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.addLayout(self.labelsLayout)
        layout.addWidget(self.slider)
        self.setLayout(layout)

        # init bindings
        self.slider.valueChanged.connect(lambda _: self.valueChanged.emit(self.value()))

    def setLabels(self, labels: List[str]):
        self.labels = labels

        nLabels = len(labels)
        self.slider.setRange(0, nLabels - 1)

        layout = self.labelsLayout
        clearLayout(layout)

        for i in range(nLabels):
            layout.addWidget(QLabel(self.labels[i]), stretch=0)

            isLast = i == (nLabels - 1)
            if not isLast:
                layout.addWidget(QWidget(), stretch=1)

    def index(self) -> int:
        return self.slider.value()

    def setIndex(self, val: int) -> None:
        self.slider.setValue(val)

    def value(self) -> Optional[str]:
        return (
            self.labels[self.index()]
            if (self.labels is not None) and (len(self.labels) >= 1)
            else None
        )


class BlockDiagramView(QGraphicsView):
    def __init__(self, *, scene: QGraphicsScene, parent: QWidget = None):
        super().__init__(scene, parent)

        self.setRenderHints(QPainter.HighQualityAntialiasing)
        self.setTransformationAnchor(QGraphicsView.NoAnchor)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setBackgroundBrush(QBrush(QColor(240, 240, 240), Qt.CrossPattern))

    def wheelEvent(self, event: QWheelEvent) -> None:
        scale = 1.25
        maxZoom = 2
        minZoom = 0.5

        transform: QTransform = self.transform()
        zoom = transform.m11()

        # zoom in and out with the mouse setting origin
        if (event.angleDelta().y() > 0) and (zoom < maxZoom):
            self.scale(scale, scale)

            pos: QPointF = self.mapToScene(event.pos())
            self.translate(-(scale - 1) * pos.x(), -(scale - 1) * pos.y())

        elif (event.angleDelta().y() < 0) and (zoom > minZoom):
            self.scale(1 / scale, 1 / scale)

            pos: QPointF = self.mapToScene(event.pos())
            self.translate(-(1 / scale - 1) * pos.x(), -(1 / scale - 1) * pos.y())

        event.accept()

    def resizeEvent(self, event: QResizeEvent):
        # resize so that the center remains constant
        dd: QSize = (event.size() - event.oldSize()) / 2
        self.translate(dd.width(), dd.height())

        super().resizeEvent(event)


class BlockDiagramEditorView(QWidget):
    _size = 1_000

    def __init__(self):
        super().__init__()

        self.labeledSlider = VLabeledSlider()

        self._qscene = QGraphicsScene()
        self._qscene.setSceneRect(
            -self._size / 2, -self._size / 2, self._size, self._size
        )

        self._qview = BlockDiagramView(scene=self._qscene, parent=self)

        layout = QHBoxLayout()
        layout.addWidget(self.labeledSlider, 0)
        layout.addWidget(self._qview, 1)
        layout.setAlignment(Qt.AlignCenter)
        self.widgetLayout = layout

        groupBox = QGroupBox()
        groupBox.setTitle("Block diagram")
        groupBox.setLayout(layout)

        parentLayout = QVBoxLayout()
        parentLayout.addWidget(groupBox)
        self.setLayout(parentLayout)


class BlockDiagramEditor:
    def __init__(self, block: Block, payloads: EventedList[Payload]):
        super().__init__()

        self.block = block
        self.payloads = payloads

        # set up Qt model/view
        self._view = BlockDiagramEditorView()

        # init bindings
        self._view.labeledSlider.valueChanged.connect(lambda _: self.update())

        self.indicators: List[Indicator] = []

        # device list bindings
        def device_added(device: Device):
            vector = Vector(pos=EventedPoint(x=0, y=0), angle=0)
            self.add_indicator(device, vector)

            self.update()

        def device_deleted(index: int):
            del block.vectors[index]
            self._view._qscene.removeItem(self.indicators[index]._item)
            del self.indicators[index]

            self.update()

        def devices_swapped(ind1: int, ind2: int):
            self.block.vectors.swap(ind1, ind2)
            (self.indicators[ind1], self.indicators[ind2]) = (
                self.indicators[ind2],
                self.indicators[ind1],
            )

            self.update()

        self.block.devices.events.added.connect(lambda d: device_added(d["item"]))
        self.block.devices.events.deleted.connect(lambda ind: device_deleted(ind))
        self.block.devices.events.swapped.connect(devices_swapped)

        # device bindings
        for device in self.block.devices:
            device.events.payload_name.connect(lambda _: self.update())

        def add_payload_bindings(payload: Payload):
            payload.formulations.events.changed.connect(lambda _: self.update())
            for formulation in payload.formulations:
                formulation.events.name.connect(lambda _: self.update())
                formulation.events.level.connect(lambda _: self.update())

        # payload bindings
        for payload in self.payloads:
            add_payload_bindings(payload)
        self.payloads.events.added.connect(lambda d: add_payload_bindings(d["item"]))

        # init
        self.init_indicators()
        self.update()

    def init_indicators(self):
        vectors = self.block.vectors
        for i, device in enumerate(self.block.devices):
            try:
                vector = vectors[i]
            except IndexError:
                vector = Vector(pos=EventedPoint(x=0, y=0), angle=0)

            self.add_indicator(device, vector)

    def add_indicator(self, device: Device, vector: Vector):
        vectors = self.block.vectors
        vectors.append(vector)

        # clip vector
        min_s = -self._view._size / 2
        max_s = self._view._size / 2

        vector.pos.x = min(max(vector.pos.x, min_s), max_s)
        vector.pos.y = min(max(vector.pos.y, min_s), max_s)

        indicator = Indicator(device, vector, self.payloads)
        self.indicators.append(indicator)
        self._view._qscene.addItem(indicator._item)

    def update(self):
        levels = get_levels(self.block, self.payloads)
        self._view.labeledSlider.setLabels(levels)

        level = self._view.labeledSlider.value()
        if level is not None:
            for indicator in self.indicators:
                indicator.update_level(level)
