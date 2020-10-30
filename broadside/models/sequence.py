from typing import Dict, Union

from napari.utils.events import EmitterGroup, Event


class SequenceModel:
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

    def __init__(self, n: int):
        self._n = n
        self._index = 0

        self.events = EmitterGroup(source=self, auto_connect=True, index=Event)

    @property
    def index(self) -> int:
        return self._index

    @index.setter
    def index(self, val: int) -> None:
        # being lenient here
        val = min(max(val, 0), self._n - 1)
        if self._index != val:
            self._index = val
            self.events.index(index=self._index)

    @property
    def first(self) -> bool:
        return self._index == 0

    @property
    def last(self) -> bool:
        return self._index == (self._n - 1)

    def move_next(self) -> None:
        self.index += 1

    def move_back(self) -> None:
        self.index -= 1

    @property
    def state(self) -> Dict[str, Union[int, str, bool]]:
        return {
            "index": self.index,
            "first": self.first,
            "last": self.last,
        }
