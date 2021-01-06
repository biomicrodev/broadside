from typing import List

from PySide2.QtCore import Qt

from .model import NavigatorModel
from .view import NavigatorWidget


class Navigator:
    def __init__(self, labels: List[str]):
        n = len(labels)

        self.model = NavigatorModel(n)
        self.view = NavigatorWidget(labels=labels)

        self.init_bindings()
        self.refresh()

    def init_bindings(self):
        self.view.backButton.clicked.connect(lambda: self.model.moveBack())
        self.view.nextButton.clicked.connect(lambda: self.model.moveNext())

        self.model.isValidChanged.connect(lambda: self.refresh())
        self.model.indexChanged.connect(lambda: self.refresh())

    def refresh(self):
        self.view.backButton.setEnabled(not self.model.first)
        self.view.backButton.setCursor(
            Qt.PointingHandCursor if (not self.model.first) else Qt.ForbiddenCursor
        )

        self.view.nextButton.setEnabled((not self.model.last) and self.model.isValid)
        self.view.nextButton.setCursor(
            Qt.PointingHandCursor
            if (not self.model.last) and self.model.isValid
            else Qt.ForbiddenCursor
        )

        self.view.setState(index=self.model.index, isComplete=self.model.isValid)
