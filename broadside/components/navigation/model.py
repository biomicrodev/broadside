import logging

from PySide2.QtCore import QObject, Signal


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
    is_valid: bool
        Whether current step is complete or not
    """

    log = logging.getLogger(__name__)

    indexChanged = Signal()
    isValidChanged = Signal()

    def __init__(self, n: int, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._n = n
        self._index = 0
        self._isValid = False

        # logging
        self.indexChanged.connect(
            lambda: self.log.info(f"Index changed to {self.index}"),
        )
        self.isValidChanged.connect(
            lambda: self.log.info(f"isValid changed to {self.isValid}"),
        )

    @property
    def index(self) -> int:
        return self._index

    @index.setter
    def index(self, val: int) -> None:
        val = min(max(val, 0), self._n - 1)  # being lenient here

        if val > self.index and self.isValid:
            self._index = val
            self.indexChanged.emit()
            return

        if val > self.index and not self.isValid:
            self.log.warning("Attempting to step ahead when incomplete")

        if val < self.index:
            self._index = val
            self.indexChanged.emit()
            return

    @property
    def isValid(self) -> bool:
        return self._isValid

    @isValid.setter
    def isValid(self, val: bool) -> None:
        if self.isValid is not val:
            self._isValid = val
            self.isValidChanged.emit()

    @property
    def first(self) -> bool:
        return self.index == 0

    @property
    def last(self) -> bool:
        return self.index == (self._n - 1)

    def moveNext(self) -> None:
        self.index += 1

    def moveBack(self) -> None:
        self.index -= 1
