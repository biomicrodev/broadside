from typing import List

from PySide2.QtWidgets import QWidget


class SequenceWidget(QWidget):
    def __init__(self, *, parent, labels: List[str]):
        super().__init__(parent=parent)

        self.labels = labels
        self._index = 0

    @property
    def index(self) -> int:
        return self._index

    @index.setter
    def index(self, val: int) -> None:
        self._index = val
