import logging

from ...utils.events import EventEmitter


class NavigatorModel:
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

    class Events:
        def __init__(self):
            self.index = EventEmitter()
            self.is_valid = EventEmitter()

    def __init__(self, n: int, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.events = self.Events()

        self._n = n
        self._index = 0
        self._is_valid = False

        # logging
        self.events.index.connect(
            lambda _: self.log.debug(f"index changed to {self.index}"),
        )
        self.events.is_valid.connect(
            lambda _: self.log.debug(f"is_valid changed to {self.is_valid}"),
        )

    @property
    def index(self) -> int:
        return self._index

    @index.setter
    def index(self, val: int) -> None:
        val = min(max(val, 0), self._n - 1)  # being lenient here

        if val > self.index:
            if self.is_valid:
                self._index = val
                self.events.index.emit(val)

            else:
                self.log.warning("Attempting to step ahead when incomplete")

        elif val < self.index:
            self._index = val
            self.events.index.emit(val)

    @property
    def is_valid(self) -> bool:
        return self._is_valid

    @is_valid.setter
    def is_valid(self, val: bool) -> None:
        if self.is_valid is not val:
            self._is_valid = val
            self.events.is_valid.emit(val)

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
