import math
import time
from typing import List, Tuple

from qtpy.QtCore import QObject, Signal, Qt, QPointF, QRectF
from qtpy.QtGui import (
    QPen,
    QMouseEvent,
    QPolygonF,
    QPainter,
    QPainterPath,
    QTextBlockFormat,
    QTextCursor,
)
from qtpy.QtWidgets import (
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
    QGraphicsObject,
)

from ....models.utils import clip_angle

AngledLabel = Tuple[str, float]


class CircleItem(QGraphicsEllipseItem):
    radius = 40

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        pen = QPen(Qt.black)
        pen.setWidth(2)
        self.setPen(pen)
        self.setRect(-self.radius, -self.radius, self.radius * 2, self.radius * 2)
        self.setCursor(Qt.OpenHandCursor)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        self.setCursor(Qt.OpenHandCursor)


class FSignal(QObject):
    """
    This is pretty awkward, but it's not possible to inherit both QGraphicsItems and
    QObjects.
    """

    changed = Signal(float)


class FiducialItem(QGraphicsPolygonItem):
    size = 16

    def __init__(self, *args, offset: float, **kwargs):
        super().__init__(*args, **kwargs)

        self.offset = offset
        self.angleSignal = FSignal()

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
        angle = math.atan2(dy, dx)
        angle = clip_angle(angle)
        angle = math.degrees(angle)

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
            labelAngle += angle

            width: float = textItem.boundingRect().width()
            height: float = textItem.boundingRect().height()

            lineItem.setLine(
                self.radius * math.cos(labelAngle),
                self.radius * math.sin(labelAngle),
                (self.radius + self.length) * math.cos(labelAngle),
                (self.radius + self.length) * math.sin(labelAngle),
            )

            textItem.setPos(
                (self.offset + width / 2) * math.cos(labelAngle) - width / 2,
                (self.offset + height / 4) * math.sin(labelAngle) - height / 2,
            )


class AlignedGraphicsTextItem(QGraphicsTextItem):
    format = QTextBlockFormat()

    def setText(self, text: str, alignment: Qt.Alignment = Qt.AlignCenter) -> None:
        super().setPlainText(text)

        self.format.setAlignment(alignment)

        cursor: QTextCursor = self.textCursor()
        cursor.select(QTextCursor.Document)
        cursor.mergeBlockFormat(self.format)
        cursor.clearSelection()

        self.setTextCursor(cursor)


class IndicatorItem(QGraphicsObject):
    indicatorChanged = Signal()

    def __init__(self, index: int, *args, initAngle: float = 0, **kwargs):
        super().__init__(*args, **kwargs)
        self._lastUpdated = None
        self.index = index

        self.setFlags(QGraphicsItem.ItemIsMovable)

        self.angle = initAngle

        self.circleItem = CircleItem(self)
        self.textItem = AlignedGraphicsTextItem(self.circleItem)
        self.labelsItem = LabelsItem(self.circleItem, radius=CircleItem.radius)

        self.fiducialItem = FiducialItem(self.circleItem, offset=CircleItem.radius)

        def angleChanged(angle: float) -> None:
            self.angle = angle

            self.fiducialItem.setAngle(angle)
            self.labelsItem.setAngle(angle)

            self.dataChangedRaw()

        self.fiducialItem.angleSignal.changed.connect(lambda angle: angleChanged(angle))
        angleChanged(self.angle)

    def setText(self, s: str) -> None:
        self.textItem.setText(s)
        self.textItem.setPos(
            -self.textItem.boundingRect().width() / 2,
            -self.textItem.boundingRect().height() / 2,
        )
        self.textItem.setTextWidth(self.textItem.boundingRect().width())

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

        self.dataChangedRaw()

    def dataChangedRaw(self):
        # really basic rate-limiting
        now = time.monotonic()
        if (self._lastUpdated is None) or (
            (self._lastUpdated is not None) and (now - self._lastUpdated > 0.00)
        ):
            self._lastUpdated = now
            self.indicatorChanged.emit()
