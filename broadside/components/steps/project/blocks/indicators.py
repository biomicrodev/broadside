import math
from dataclasses import dataclass
from typing import List, Optional

from qtpy.QtCore import QRectF, Qt, QPointF, Signal
from qtpy.QtGui import (
    QPainter,
    QPen,
    QColor,
    QPolygonF,
    QMouseEvent,
    QTextBlockFormat,
    QTextCursor,
    QPainterPath,
)
from qtpy.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsSceneMouseEvent,
    QGraphicsPolygonItem,
    QGraphicsItem,
    QGraphicsItemGroup,
    QGraphicsTextItem,
    QGraphicsObject,
    QStyleOptionGraphicsItem,
    QGraphicsLineItem,
    QWidget,
    QGraphicsScene,
    QLabel,
)

from .....models.block import Vector, Device
from .....models.payload import Payload
from .....utils.events import EventedList, EventEmitter
from .....utils.geom import Angle


@dataclass(frozen=True)
class AngledText:
    text: str
    rel_angle: Angle


class CircleItem(QGraphicsEllipseItem):
    def __init__(
        self,
        *,
        radius: float = 40,
        width: float = 2,
        color: QColor = Qt.black,
        parent: QGraphicsItem = None,
    ):
        super().__init__(parent)

        self.radius = radius
        pen = QPen(color)
        pen.setWidth(width)
        self.setPen(pen)
        self.setRect(-radius, -radius, radius * 2, radius * 2)
        self.setCursor(Qt.OpenHandCursor)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        self.setCursor(Qt.OpenHandCursor)


class FiducialItem(QGraphicsPolygonItem):
    class Events:
        def __init__(self):
            self.angle = EventEmitter()

    def __init__(
        self,
        *,
        offset: float,
        size: int = 16,
        color: QColor = Qt.black,
        parent: QGraphicsItem = None,
    ):
        super().__init__(parent)

        self.events = self.Events()

        self.offset = offset

        self.setBrush(color)
        self.setFlags(self.flags() | QGraphicsItem.ItemIsMovable)
        self.setCursor(Qt.OpenHandCursor)

        points = [(size, 0), (0, size / 2), (0, -size / 2)]
        polygon = QPolygonF([QPointF(x, y) for x, y in points])
        self.setPolygon(polygon)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        self.setCursor(Qt.OpenHandCursor)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        parent: QGraphicsItem = self.parentItem()
        center: QPointF = parent.scenePos()
        pos: QPointF = event.scenePos()

        dy = pos.y() - center.y()
        dx = pos.x() - center.x()
        angle = math.atan2(dy, dx)
        angle = Angle(rad=angle)

        self._setAngle(angle)
        self.events.angle.emit(angle)

    def _setAngle(self, angle: Angle) -> None:
        self.setRotation(angle.deg)
        self.setPos(
            self.offset * math.cos(angle.rad), self.offset * math.sin(angle.rad)
        )


class LabelsItem(QGraphicsItemGroup):
    def __init__(
        self,
        *,
        radius: float,
        offset: float = 60,
        length: float = 15,
        parent: QGraphicsItem = None,
    ):
        super().__init__(parent)

        self.radius = radius
        self.offset = offset
        self.length = length

        self._angledTexts: List[AngledText] = []
        self._lineItems: List[QGraphicsLineItem] = []
        self._textItems: List[QGraphicsTextItem] = []

    def setAngledTexts(self, angledTexts: List[AngledText]) -> None:
        self._angledTexts = angledTexts

        self._lineItems.clear()
        self._textItems.clear()

        scene: QGraphicsScene = self.scene()
        for item in self.childItems():
            item: QGraphicsItem = item
            self.removeFromGroup(item)
            if scene is not None:
                scene.removeItem(item)

        for angledText in self._angledTexts:
            lineItem = QGraphicsLineItem(self.parentItem())
            self.addToGroup(lineItem)
            self._lineItems.append(lineItem)

            textItem = QGraphicsTextItem(self.parentItem())
            textItem.setPlainText(angledText.text)
            self.addToGroup(textItem)
            self._textItems.append(textItem)

    def setAngle(self, angle: Angle) -> None:
        for textItem, lineItem, angledText in zip(
            self._textItems, self._lineItems, self._angledTexts
        ):
            totAngle = (angledText.rel_angle + angle).rad

            lineItem.setLine(
                self.radius * math.cos(totAngle),
                self.radius * math.sin(totAngle),
                (self.radius + self.length) * math.cos(totAngle),
                (self.radius + self.length) * math.sin(totAngle),
            )

            width: float = textItem.boundingRect().width()
            height: float = textItem.boundingRect().height()
            textItem.setPos(
                (self.offset + width / 2) * math.cos(totAngle) - width / 2,
                (self.offset + height / 4) * math.sin(totAngle) - height / 2,
            )


class AlignedGraphicsTextItem(QGraphicsTextItem):
    format = QTextBlockFormat()

    def setText(self, text: str, alignment: Qt.Alignment = Qt.AlignCenter) -> None:
        super().setPlainText(text)

        rect: QRectF = self.boundingRect()
        self.setPos(-rect.width() / 2, -rect.height() / 2)

        self.format.setAlignment(alignment)

        cursor: QTextCursor = self.textCursor()
        cursor.select(QTextCursor.Document)
        cursor.mergeBlockFormat(self.format)
        cursor.clearSelection()
        self.setTextCursor(cursor)


class IndicatorItem(QGraphicsObject):
    moved = Signal(int, int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setFlags(self.flags() | QGraphicsItem.ItemIsMovable)

        self.circleItem = CircleItem()
        self.circleItem.setParentItem(self)

        self.textItem = AlignedGraphicsTextItem()
        self.textItem.setParentItem(self.circleItem)

        self.labelsItem = LabelsItem(radius=self.circleItem.radius)
        self.labelsItem.setParentItem(self.circleItem)

        self.fiducialItem = FiducialItem(offset=self.circleItem.radius)
        self.fiducialItem.setParentItem(self.circleItem)

    def boundingRect(self) -> QRectF:
        return self.circleItem.boundingRect()

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget,
        *args,
        **kwargs,
    ):
        pass

    def shape(self):
        path = QPainterPath()
        path.addEllipse(self.boundingRect())
        return path

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseMoveEvent(event)

        if event.buttons() & Qt.LeftButton:
            scene: QGraphicsScene = self.scene()
            rect: QRectF = scene.sceneRect()
            min_x = rect.x()
            min_y = rect.y()
            max_x = min_x + rect.width()
            max_y = min_y + rect.height()

            pos: QPointF = self.pos()
            old_x = pos.x()
            old_y = pos.y()
            new_x = min(max(old_x, min_x), max_x)
            new_y = min(max(old_y, min_y), max_y)
            new_x = int(round(new_x))
            new_y = int(round(new_y))

            self.setPos(new_x, new_y)
            self.moved.emit(new_x, new_y)


class Indicator:
    def __init__(self, device: Device, vector: Vector, payloads: EventedList[Payload]):
        self.device = device
        self.vector = vector
        self.payloads = payloads

        self._item = IndicatorItem()

        # angle bindings
        def angle_updated(angle: Angle):
            vector.angle.rad = angle.rad
            self._item.fiducialItem._setAngle(angle)
            self._item.labelsItem.setAngle(vector.angle)

        self._item.fiducialItem.events.angle.connect(angle_updated)
        self._item.fiducialItem._setAngle(vector.angle)
        self._item.labelsItem.setAngle(vector.angle)

        # position bindings
        def update_pos(x: int, y: int):
            vector.pos.x = x
            vector.pos.y = y

        self._item.moved.connect(update_pos)
        self._item.setPos(vector.pos.x, vector.pos.y)

        # name bindings
        device.events.name.connect(lambda _: self.update_name())
        device.events.sample_name.connect(lambda _: self.update_name())
        device.events.payload_name.connect(lambda _: self.update_name())
        self.update_name()

    def update_name(self):
        device_name = self.device.name
        sample_name = self.device.sample_name
        payload_name = self.device.payload_name
        self._item.textItem.setText("\n".join([device_name, sample_name, payload_name]))

    def update_level(self, level: str):
        payload_name = self.device.payload_name

        payload: Optional[Payload] = next(
            (p for p in self.payloads if p.name == payload_name), None
        )
        if payload is None:
            self._item.labelsItem.setAngledTexts([])
            self._item.fiducialItem.hide()

        else:
            angled_texts: List[AngledText] = [
                AngledText(rel_angle=f.angle, text=f.name)
                for f in payload.formulations
                if f.level == level
            ]
            self._item.labelsItem.setAngledTexts(angled_texts)
            self._item.labelsItem.setAngle(self.vector.angle)
            if len(angled_texts) != 0:
                self._item.fiducialItem.show()
            else:
                self._item.fiducialItem.hide()
