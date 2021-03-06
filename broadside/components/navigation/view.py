from enum import Enum, auto
from typing import List

from qtpy.QtCore import Qt, QPointF, QEvent
from qtpy.QtGui import QPainter, QPen, QPolygonF, QColor
from qtpy.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QLabel,
)

from ...utils.colors import Color


class StepStatus(Enum):
    Incomplete = auto()
    InProgress = auto()
    Complete = auto()


class IndexWidget(QWidget):
    indexLabelColors = {
        StepStatus.Incomplete: Color.White.css(),
        StepStatus.InProgress: Color.White.css(),
        StepStatus.Complete: Color.White.css(),
    }

    indexBackgroundColors = {
        StepStatus.Incomplete: Color.Gray.css(),
        StepStatus.InProgress: Color.Blue.css(),
        StepStatus.Complete: Color.Green.css(),
    }

    textColors = {
        StepStatus.Incomplete: Color.Gray.css(),
        StepStatus.InProgress: Color.Black.css(),
        StepStatus.Complete: Color.Black.css(),
    }

    def __init__(
        self,
        text: str,
        index: int,
        state: StepStatus = StepStatus.Incomplete,
        parent: QWidget = None,
    ):
        super().__init__(parent)

        self._text = text
        self._index = index

        self.initUI()
        self.setState(state)

    def initUI(self) -> None:
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        indexLabel = QLabel()
        indexLabel.setText(str(self._index))
        indexLabel.setFixedSize(20, 20)
        indexLabel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        indexLabel.setAlignment(Qt.AlignCenter)
        self.indexLabel = indexLabel

        textLabel = QLabel()
        textLabel.setText(self._text)
        textLabel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        textLabel.setAlignment(Qt.AlignCenter)
        self.textLabel = textLabel

        layout = QHBoxLayout()
        layout.addWidget(indexLabel)
        layout.addWidget(textLabel)
        self.setLayout(layout)

    def setState(self, state: StepStatus) -> None:
        indexLabelStyleSheet = (
            "border-radius: 10px;"  # half of label size
            f"background-color: {self.indexBackgroundColors[state]};"
            f"color: {self.indexLabelColors[state]};"
        )
        self.indexLabel.setStyleSheet(indexLabelStyleSheet)

        textLabelStyleSheet = f"color: {self.textColors[state]}"
        self.textLabel.setStyleSheet(textLabelStyleSheet)


class StepProgress(Enum):
    Enabled = auto()
    Disabled = auto()


class ChevronWidget(QWidget):
    colors = {
        StepProgress.Enabled: Color.Black,
        StepProgress.Disabled: Color.Gray,
    }

    def __init__(self, *args, state: StepProgress = StepProgress.Disabled, **kwargs):
        super().__init__(*args, **kwargs)

        self._state: StepProgress = state

        self.setFixedSize(20, 20)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.initCoords()

    def initCoords(self):
        w = 10
        h = 10
        r = 6
        coords = [(-r / 2, r), (r / 2, 0), (-r / 2, -r)]
        coords = [(x + w, y + h) for x, y in coords]
        coords = [QPointF(x, y) for x, y in coords]
        coords = QPolygonF(coords)
        self.coords = coords

    def paintEvent(self, event: QEvent) -> None:
        color = self.colors[self._state]
        color = QColor(*(color.value))

        painter = QPainter(self)
        painter.setRenderHint(QPainter.HighQualityAntialiasing)
        painter.setPen(QPen(color, 2))
        painter.drawPolyline(self.coords)

        event.accept()

    def setState(self, val: StepProgress) -> None:
        self._state = val
        self.update()


class NavigatorWidget(QWidget):
    def __init__(self, labels: List[str], *args, **kwargs):
        super().__init__(*args, **kwargs)

        if len(labels) < 2:
            raise ValueError(
                "Number of steps in NavigationWidget must be greater or equal to 2! "
                f"Length {len(labels)} passed"
            )

        self.labels = labels

        self.indexWidgets: List[IndexWidget] = []
        self.chevronWidgets: List[ChevronWidget] = []

        self.initLayout()
        self.setState(index=0, is_complete=False)

    def initLayout(self):
        sequenceLayout = QHBoxLayout()
        sequenceLayout.setSpacing(0)
        sequenceLayout.setContentsMargins(0, 0, 0, 0)

        for i, label in enumerate(self.labels):
            indexWidget = IndexWidget(text=label, index=(i + 1))
            self.indexWidgets.append(indexWidget)
            sequenceLayout.addWidget(indexWidget, stretch=0)

            isLast = i == (len(self.labels) - 1)
            if not isLast:
                chevronWidget = ChevronWidget()
                self.chevronWidgets.append(chevronWidget)
                sequenceLayout.addWidget(chevronWidget, stretch=0)

        # navigation buttons
        backButton = QPushButton()
        backButton.setText("Back")
        backButton.setObjectName("backButton")
        self.backButton = backButton

        nextButton = QPushButton()
        nextButton.setText("Next")
        nextButton.setObjectName("nextButton")
        self.nextButton = nextButton

        buttonsLayout = QHBoxLayout()
        buttonsLayout.addWidget(backButton)
        buttonsLayout.addWidget(nextButton)
        buttonsLayout.setContentsMargins(0, 0, 0, 0)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch(1)
        layout.addLayout(sequenceLayout)
        layout.addSpacing(30)
        layout.addLayout(buttonsLayout)
        layout.addSpacing(20)

        self.setLayout(layout)

    def setState(self, *, index: int, is_complete: bool) -> None:
        if (index < 0) or (index >= len(self.labels)):
            raise IndexError(f"Index {index} out of bounds; length {len(self.labels)}")

        for i in range(len(self.labels)):
            if i < index:
                state = StepStatus.Complete
            elif i == index:
                state = StepStatus.Complete if is_complete else StepStatus.InProgress
            else:
                state = StepStatus.Incomplete

            self.indexWidgets[i].setState(state)

        for i in range(len(self.labels) - 1):
            if i < index:
                state = StepProgress.Enabled
            elif i == index:
                state = StepProgress.Enabled if is_complete else StepProgress.Disabled
            else:
                state = StepProgress.Disabled

            self.chevronWidgets[i].setState(state)
