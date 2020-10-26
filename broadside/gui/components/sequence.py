from typing import List

from PySide2.QtWidgets import QWidget


class SequenceWidget(QWidget):
    def __init__(self, *, parent, labels: List[str]):
        super().__init__(parent=parent)

        self.labels = labels
