from abc import ABC

from .events import EventEmitter


class Validatable(ABC):
    class Events:
        def __init__(self):
            self.is_valid = EventEmitter()

    def __init__(self):
        self.events = self.Events()

        self._is_valid: bool = False

    @property
    def is_valid(self) -> bool:
        return self._is_valid

    @is_valid.setter
    def is_valid(self, val: bool) -> None:
        if self.is_valid is not val:
            self._is_valid = val
            self.events.is_valid.emit(val)

    def validate(self) -> None:
        raise NotImplementedError
