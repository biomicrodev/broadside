import logging

from PySide2.QtCore import Signal, QObject


class NavigatorModel(QObject):
    """
    Maneuvering along a sequence of steps.

    Parameters
    ----------
    n: int
        Number of steps

    Attributes
    ----------
    index: int
        Current index
    first: bool
        At the beginning of the sequence
    last: bool
        At the end of the sequence
    isComplete: bool
        Whether current step is complete or not
    """

    log = logging.getLogger(__name__)

    # model to view
    indexChanged = Signal()
    isCompleteChanged = Signal()

    def __init__(self, n: int, isComplete: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._n = n
        self._index = 0
        self._isComplete = isComplete

        # logging
        self.indexChanged.connect(
            lambda: self.log.info(f"Index changed to {self.index}")
        )
        self.isCompleteChanged.connect(
            lambda: self.log.info(f"isComplete changed to {self.isComplete}")
        )

    @property
    def index(self) -> int:
        return self._index

    @index.setter
    def index(self, val: int) -> None:
        val = min(max(val, 0), self._n - 1)  # being lenient here

        if val > self.index and self.isComplete:
            self._index = val
            self.indexChanged.emit()
            return

        if val > self.index and not self.isComplete:
            self.log.warning("Attempting to step ahead when incomplete")

        if val < self.index:
            self._index = val
            self.indexChanged.emit()
            return

    @property
    def isComplete(self) -> bool:
        return self._isComplete

    @isComplete.setter
    def isComplete(self, val: bool) -> None:
        if self.isComplete is not val:
            self._isComplete = val
            self.isCompleteChanged.emit()

    @property
    def first(self) -> bool:
        return self.index == 0

    @property
    def last(self) -> bool:
        return self.index == (self._n - 1)

    def move_next(self) -> None:
        self.index += 1

    def move_back(self) -> None:
        self.index -= 1
