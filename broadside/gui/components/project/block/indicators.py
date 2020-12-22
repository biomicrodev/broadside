import math
import time
from typing import List, Tuple

from PySide2.QtCore import QObject, Signal, Qt, QPointF, QRectF
from PySide2.QtGui import QPen, QMouseEvent, QPolygonF, QPainter, QPainterPath
from PySide2.QtWidgets import (
    QWidget,
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsPolygonItem,
    QGraphicsSceneMouseEvent,
    QGraphicsItemGroup,
    QGraphicsTextItem,
    QStyleOptionGraphicsItem,
    QGraphicsScene,
    QGraphicsLineItem,
)

AngledLabel = Tuple[str, float]


class EmptySignal(QObject):
    """
    We need these weird class because multiple inheritance with Qt (that is, a class
    that inherits from both QGraphicsItem and QObject) throws some kind of segfault.
    """

    changed = Signal()


class FloatSignal(QObject):
    changed = Signal(float)


class CircleItem(QGraphicsEllipseItem):
    radius = 40

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        pen = QPen(Qt.black)
        pen.setWidth(2)
        self.setPen(pen)
        self.setRect(-self.radius, -self.radius, self.radius * 2, self.radius * 2)
        self.setCursor(Qt.OpenHandCursor)

        self.dataChanged = EmptySignal()

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        self.setCursor(Qt.OpenHandCursor)


class FiducialItem(QGraphicsPolygonItem):
    size = 16

    def __init__(self, *args, offset: float, angleSignal: FloatSignal, **kwargs):
        super().__init__(*args, **kwargs)

        self.offset = offset
        self.angleSignal = angleSignal

        self.setBrush(Qt.black)
        self.setFlags(QGraphicsItem.ItemIsMovable)
        self.setCursor(Qt.OpenHandCursor)

        points = [(self.size, 0), (0, self.size / 2), (0, -self.size / 2)]
        polygon = QPolygonF([QPointF(x, y) for x, y in points])
        self.setPolygon(polygon)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        self.setCursor(Qt.OpenHandCursor)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        circle: CircleItem = self.parentItem()
        center: QPointF = circle.scenePos()
        pos: QPointF = event.scenePos()

        dy = pos.y() - center.y()
        dx = pos.x() - center.x()
        angle = math.degrees(math.atan2(dy, dx))

        angle = math.fmod(angle, 360.0)
        if angle < 0.0:
            angle += 360.0
        angle = round(angle)

        self.setAngle(angle)
        self.angleSignal.changed.emit(angle)

    def setAngle(self, angle: float) -> None:
        # angle is in degrees
        self.setRotation(angle)

        angle = math.radians(angle)
        self.setPos(self.offset * math.cos(angle), self.offset * math.sin(angle))


class LabelsItem(QGraphicsItemGroup):
    offset = 60
    length = 15

    def __init__(self, *args, radius: float, **kwargs):
        super().__init__(*args, **kwargs)

        self.radius = radius
        self.angledLabels: List[AngledLabel] = []

        self.lineItems: List[QGraphicsLineItem] = []
        self.textItems: List[QGraphicsTextItem] = []

    def setLabels(self, labels: List[AngledLabel], angle: float) -> None:
        self.angledLabels = labels
        angle = math.radians(angle)

        self.lineItems.clear()
        self.textItems.clear()

        scene: QGraphicsScene = self.scene()
        for item in self.childItems():
            item: QGraphicsItem = item
            self.removeFromGroup(item)
            if scene is not None:
                scene.removeItem(item)

        for label, labelAngle in self.angledLabels:
            labelAngle = math.radians(labelAngle)

            lineItem = QGraphicsLineItem(self.parentItem())
            lineItem.setLine(
                self.radius * math.cos(labelAngle + angle),
                self.radius * math.sin(labelAngle + angle),
                (self.radius + self.length) * math.cos(labelAngle + angle),
                (self.radius + self.length) * math.sin(labelAngle + angle),
            )
            self.addToGroup(lineItem)
            self.lineItems.append(lineItem)

            textItem = QGraphicsTextItem(self.parentItem())
            textItem.setPlainText(label)
            width = textItem.boundingRect().width()
            height = textItem.boundingRect().height()
            textItem.setPos(
                (self.offset + width / 2) * math.cos(labelAngle + angle) - width / 2,
                (self.offset + height / 4) * math.sin(labelAngle + angle) - height / 2,
            )
            self.addToGroup(textItem)
            self.textItems.append(textItem)

    def setAngle(self, angle: float) -> None:
        angle = math.radians(angle)

        for textItem, lineItem, (label, labelAngle) in zip(
            self.textItems, self.lineItems, self.angledLabels
        ):
            labelAngle = math.radians(labelAngle)

            width = textItem.boundingRect().width()
            height = textItem.boundingRect().height()
            textItem.setPos(
                (self.offset + width / 2) * math.cos(labelAngle + angle) - width / 2,
                (self.offset + height / 4) * math.sin(labelAngle + angle) - height / 2,
            )

            lineItem.setLine(
                self.radius * math.cos(labelAngle + angle),
                self.radius * math.sin(labelAngle + angle),
                (self.radius + self.length) * math.cos(labelAngle + angle),
                (self.radius + self.length) * math.sin(labelAngle + angle),
            )


class IndicatorItem(QGraphicsItem):
    def __init__(self, index: int, *args, initAngle: float = 0, **kwargs):
        super().__init__(*args, **kwargs)
        self._lastUpdated = None
        self.index = index

        self.setFlags(QGraphicsItem.ItemIsMovable)

        self.angle = initAngle
        self.angleSignal = FloatSignal()
        self.emptySignal = EmptySignal()  # naming these things sucks

        self.circleItem = CircleItem(self)
        self.textItem = QGraphicsTextItem(self.circleItem)
        self.labelsItem = LabelsItem(self.circleItem, radius=CircleItem.radius)
        self.fiducialItem = FiducialItem(
            self.circleItem, offset=CircleItem.radius, angleSignal=self.angleSignal
        )

        def angleChanged(angle):
            self.angle = angle

            self.fiducialItem.setAngle(angle)
            self.labelsItem.setAngle(angle)

            self.dataChanged()

        self.circleItem.dataChanged.changed.connect(self.emptySignal.changed.emit)

        self.angleSignal.changed.connect(lambda angle: angleChanged(angle))
        angleChanged(self.angle)

    def setText(self, s: str) -> None:
        self.textItem.setPlainText(s)
        self.textItem.setPos(
            -self.textItem.boundingRect().width() / 2,
            -self.textItem.boundingRect().height() / 2,
        )

    def setAngledLabels(self, labels: List[AngledLabel]):
        self.labelsItem.setLabels(labels, self.angle)
        self.fiducialItem.setAngle(self.angle)
        self.labelsItem.setAngle(self.angle)

    def boundingRect(self) -> QRectF:
        return QRectF(
            -CircleItem.radius,
            -CircleItem.radius,
            CircleItem.radius * 2,
            CircleItem.radius * 2,
        )

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget,
        *args,
        **kwargs
    ):
        pass

    def shape(self):
        path = QPainterPath()
        path.addEllipse(self.boundingRect())
        return path

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        super().mouseMoveEvent(event)

        from .blockdiagram import BlockDiagramView

        view: BlockDiagramView = self.scene().views()[0]
        width = view.width()
        height = view.height()

        x = self.scenePos().x()
        y = self.scenePos().y()
        if x < 0:
            x = 0
        elif x >= width:
            x = width
        if y < 0:
            y = 0
        elif y >= height:
            y = height
        self.setPos(x, y)

        self.dataChanged()

    def dataChanged(self):
        # really basic rate-limiting
        now = time.monotonic()
        if (self._lastUpdated is None) or (
            (self._lastUpdated is not None) and (now - self._lastUpdated > 0.1)
        ):
            self._lastUpdated = now
            self.emptySignal.changed.emit()
