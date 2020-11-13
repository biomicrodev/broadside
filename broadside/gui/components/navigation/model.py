from typing import Dict, Any

from PySide2.QtCore import Signal, QObject


class NavigationModel(QObject):
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
    """

    # model to view
    indexChanged = Signal()

    def __init__(self, n: int, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._n = n
        self._index = 0

    @property
    def index(self) -> int:
        return self._index

    @index.setter
    def index(self, val: int) -> None:
        val = min(max(val, 0), self._n - 1)  # being lenient here

        if self._index != val:
            self._index = val
            self.indexChanged.emit()

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

    @property
    def state(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "first": self.first,
            "last": self.last,
        }

    def __str__(self) -> str:
        return str(self.state)
