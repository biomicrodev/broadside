from PySide2.QtCore import Qt
from PySide2.QtGui import QFontMetrics
from PySide2.QtWidgets import QFrame, QLabel


class QHLine(QFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Plain)


class QElidedLabel(QLabel):
    def setText(self, text: str):
        metrics = QFontMetrics(self.font())
        elidedText: str = metrics.elidedText(text, Qt.ElideMiddle, self.width())
        super().setText(elidedText)
