from typing import List

from qtpy.QtCore import Qt

from .model import NavigatorModel
from .view import NavigatorWidget


class Navigator:
    def __init__(self, *, labels: List[str]):
        n = len(labels)

        self.model = NavigatorModel(n)
        self._view = NavigatorWidget(labels=labels)

        self.init_bindings()
        self.refresh()

    def init_bindings(self):
        self._view.backButton.clicked.connect(lambda _: self.model.move_back())
        self._view.nextButton.clicked.connect(lambda _: self.model.move_next())

        self.model.events.is_valid.connect(lambda _: self.refresh())
        self.model.events.index.connect(lambda _: self.refresh())

    def refresh(self):
        self._view.backButton.setDisabled(self.model.first)
        self._view.backButton.setCursor(
            Qt.PointingHandCursor if (not self.model.first) else Qt.ForbiddenCursor
        )

        self._view.nextButton.setEnabled((not self.model.last) and self.model.is_valid)
        self._view.nextButton.setCursor(
            Qt.PointingHandCursor
            if (not self.model.last) and self.model.is_valid
            else Qt.ForbiddenCursor
        )

        self._view.setState(index=self.model.index, is_complete=self.model.is_valid)
