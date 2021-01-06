from typing import List

from PySide2.QtCore import Qt, Signal
from PySide2.QtGui import QPainter
from PySide2.QtWidgets import (
    QWidget,
    QGraphicsScene,
    QGraphicsView,
    QSizeGrip,
    QVBoxLayout,
    QGroupBox,
    QHBoxLayout,
    QSlider,
    QGridLayout,
    QLabel,
)
from natsort import natsorted

from .indicator import IndicatorItem, AngledLabel
from ....models.block import Block, Vector
from ....models.device import Device


def get_levels(block: Block, devices: List[Device]) -> List[str]:
    device_names = [s.device_name for s in block.samples]
    payloads = []
    for d in devices:
        if d.name in device_names:
            payloads.extend(d.payload)
    levels = [p.level for p in payloads]
    levels = list(set(levels))
    levels = natsorted(levels)
    return levels


class Slider(QSlider):
    def __init__(self, n: int, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setRange(0, n - 1)
        self.setSingleStep(1)
        self.setTickInterval(1)
        self.setPageStep(1)
        self.setOrientation(Qt.Vertical)
        self.setTickPosition(QSlider.TicksLeft)
        self.setInvertedControls(True)
        self.setInvertedAppearance(True)


class LabeledSlider(QWidget):
    def __init__(self, labels: List[str], *args, value: int = 0, **kwargs):
        super().__init__(*args, **kwargs)

        self.labels = labels

        nLabels = len(self.labels)
        self.slider = Slider(nLabels)
        self.slider.setValue(value)

        layout = QGridLayout()
        layout.setSpacing(1)

        for i in range(nLabels):
            layout.addWidget(QLabel(self.labels[i]), 2 * i, 0, 1, 1)
            layout.setRowStretch(2 * i, 0)

            isLast = i == (nLabels - 1)
            if not isLast:
                layout.addWidget(QWidget(), 2 * i + 1, 0, 1, 1)
                layout.setRowStretch(2 * i + 1, 1)

        layout.addWidget(self.slider, 0, 1, 2 * nLabels - 1, 1)

        self.setLayout(layout)

    @property
    def value(self) -> int:
        return self.slider.value()

    @value.setter
    def value(self, val: int) -> None:
        self.slider.setValue(val)

    @property
    def label(self) -> str:
        return self.labels[self.value] if self.labels else ""


class BlockDiagramScene(QGraphicsScene):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setSceneRect(0, 0, 1600, 1000)  # xywh


class BlockDiagramView(QGraphicsView):
    def __init__(self, scene: QGraphicsScene, parent: QWidget = None):
        super().__init__(scene, parent)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWindowFlag(Qt.SubWindow)
        # self.setMinimumWidth(200)
        # self.setMaximumWidth(600)
        # self.setMinimumHeight(200)
        # self.setMaximumHeight(600)
        self.setRenderHints(QPainter.Antialiasing)
        self.setBackgroundBrush(Qt.white)
        self.setTransformationAnchor(QGraphicsView.NoAnchor)
        self.setResizeAnchor(QGraphicsView.NoAnchor)
        self.setGeometry(0, 0, 748, 538)
        self.verticalScrollBar().setEnabled(False)
        self.horizontalScrollBar().setEnabled(False)


class BlockDiagramWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.scene = BlockDiagramScene()
        view = BlockDiagramView(self.scene, self)
        self.view = view

        sizeGrip = QSizeGrip(view)
        layout = QVBoxLayout(view)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(sizeGrip, alignment=Qt.AlignBottom | Qt.AlignRight)

        # self.setGeometry(0, 0, 500, 500)


class BlockDiagramEditorView(QGroupBox):
    """
    How to populate this widget, using the current block and the devices:

    for sample in block.samples:
        construct indicator
        set indicator text (sample name + device name)
        set indicator angle
        set indicator labels (drug name at angle + indicator angle)
        add indicator to scene

    The reactivity:

    from block diagram editor to model:
        whenever indicator is dragged:
            update block.samples[index].vector.pos
        whenever indicator fiducial is dragged:
            update block.samples[index].vector.angle

    from model to block diagram editor:
        whenever new sample is added:
            add to block.samples, with pos set to midpoint and angle set to 0
        whenever sample is deleted:
            delete from block.samples[index]
        whenever sample's device is changed:
            refresh view

    I really need to rethink the event system here. Signals should support what kind of
    signals they are.
    """

    blockChanged = Signal()
    refreshRequested = Signal()

    def __init__(self, block: Block, devices: List[Device], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.block = block
        self.devices = devices

        self.refreshRequested.connect(lambda: print("refresh requested"))

        levels = get_levels(self.block, self.devices)
        self.sliderWidget = LabeledSlider(levels)
        self.sliderWidget.slider.valueChanged.connect(lambda: self.updateLevel())
        self.diagramWidget = BlockDiagramWidget()

        # UI
        layout = QHBoxLayout()
        layout.addWidget(self.sliderWidget, 0)
        layout.addWidget(self.diagramWidget, 1)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.setTitle("Block Diagram")
        self.setContentsMargins(0, 0, 0, 0)

        self.initIndicators()

    def initIndicators(self):
        view: BlockDiagramView = self.diagramWidget.scene.views()[0]
        width = view.width()
        height = view.height()
        center = (width / 2, height / 2)

        level = self.sliderWidget.label
        self.diagramWidget.scene.clear()

        self.indicators: List[IndicatorItem] = []

        for i in range(len(self.block.samples)):
            sample = self.block.samples[i]
            vector = sample.vector

            deviceName = sample.device_name
            device = next((d for d in self.devices if d.name == deviceName), None)
            angledLabels: List[AngledLabel] = (
                [
                    (f.name, f.angle)
                    for f in device.payload
                    if (
                        (f.level == level)
                        and ((f.name is not None) or (f.name != ""))
                        and (f.angle is not None)
                    )
                ]
                if (device is not None)
                else []
            )

            # TODO: refactor points from List[int] to a dataclass
            if vector.pos[0] is None:
                vector.pos[0] = center[0]
            if vector.pos[1] is None:
                vector.pos[1] = center[1]

            # clip outside positions to max value
            if vector.pos[0] > width:
                vector.pos[0] = width
            if vector.pos[1] > height:
                vector.pos[1] = height

            indicator = IndicatorItem(i)
            self.diagramWidget.scene.addItem(indicator)
            self.indicators.append(indicator)

            indicator.setText(sample.name + "\n" + device.name)
            indicator.angle = vector.angle  # mixing Qt and python here...
            indicator.setAngledLabels(angledLabels)
            indicator.setPos(vector.pos[0], vector.pos[1])

            def update(indicator: IndicatorItem):
                # need to maintain reference to indicator
                vector = self.block.samples[indicator.index].vector
                vector.pos = (
                    int(indicator.pos().x()),
                    int(indicator.pos().y()),
                )
                vector.angle = indicator.angle
                self.blockChanged.emit()

            indicator.indicatorChanged.connect(lambda ind=indicator: update(ind))

    def updateLevel(self):
        level = self.sliderWidget.label

        for i, sample in enumerate(self.block.samples):
            deviceName = sample.device_name
            device = next(d for d in self.devices if d.name == deviceName)
            angledLabels: List[AngledLabel] = [
                (f.name, f.angle) for f in device.payload if f.level == level
            ]

            indicator = self.indicators[i]
            indicator.setAngledLabels(angledLabels)

    def updateSlider(self) -> None:
        levels = get_levels(self.block, self.devices)
        currentValue = self.sliderWidget.value

        # remove old slider
        layout: QHBoxLayout = self.layout()
        layout.removeWidget(self.sliderWidget)
        self.sliderWidget.deleteLater()

        # create new slider
        self.sliderWidget = LabeledSlider(levels)
        self.sliderWidget.value = currentValue
        layout.insertWidget(0, self.sliderWidget)

        self.sliderWidget.slider.valueChanged.connect(lambda: self.updateLevel())
        self.updateLevel()

    def refresh(self):
        self.initIndicators()
        self.updateSlider()
