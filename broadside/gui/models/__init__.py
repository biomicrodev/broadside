from PySide2.QtCore import QObject, Signal


class QStaleableObject(QObject):
    """
    A simple QObject that indicates whether it is stale or not. To use this object,
    connect to the `isStaleChanged` signal and set `isStale` appropriately.
    """

    isStaleChanged = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._isStale = False

    @property
    def stale(self) -> bool:
        return self._isStale

    @stale.setter
    def stale(self, val: bool) -> None:
        if self.stale is not val:
            self._isStale = val
            self.isStaleChanged.emit()
