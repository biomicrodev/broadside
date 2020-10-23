from typing import List


class SequenceModel:
    """
    Maneuvering along a sequence of steps.

    Parameters
    ----------
    labels: List[str]
        Step names

    Attributes
    ----------
    label: str
        Label corresponding to current index
    index: int
        Current index
    first: bool
        At the beginning of the sequence
    last: bool
        At the end of the sequence
    """

    def __init__(self, labels: List[str]):
        self.labels = labels
        self._index = 0

    @property
    def label(self) -> str:
        return self.labels[self._index]

    @property
    def index(self) -> int:
        return self._index

    @index.setter
    def index(self, val: int) -> None:
        # be lenient here
        self._index = min(max(val, 0), len(self.labels) - 1)

    @property
    def first(self) -> bool:
        return self._index == 0

    @property
    def last(self) -> bool:
        return self._index == (len(self.labels) - 1)

    def move_next(self) -> None:
        self.index += 1

    def move_back(self) -> None:
        self.index -= 1
