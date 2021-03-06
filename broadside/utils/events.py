"""
Keeping events simple for now. I would use napari's EventedList, but that seems a bit
complicated for my use case.
"""
import math
from collections import UserList
from typing import (
    MutableSequence,
    MutableMapping,
    TypeVar,
    Callable,
    Any,
    Optional,
    Tuple,
)

from rx.subject import Subject

from .geom import PointF, clip_angle, Angle

T = TypeVar("T")
U = TypeVar("U")


class EventEmitter(Subject):
    def connect(self, cb: Callable) -> None:
        self.subscribe(cb)

    def emit(self, value: Optional[Any] = None) -> None:
        self.on_next(value)

    def block(self) -> None:
        self.is_stopped = True

    def unblock(self) -> None:
        self.is_stopped = False


class EventedList(MutableSequence[T]):
    """
    An evented, typed version of built-in list. Follows the same convention as UserList.
    """

    class Events:
        def __init__(self):
            self.changed = EventEmitter()

            self.added = EventEmitter()  # emits dict with 'item', 'index' keys
            self.added.connect(lambda _: self.changed.emit())

            self.deleted = EventEmitter()  # emits int
            self.deleted.connect(lambda _: self.changed.emit())

            self.swapped = EventEmitter()  # emits tuple of ints of len 2
            self.swapped.connect(lambda _: self.changed.emit())

    def __init__(self, initlist=None):
        self.data = []
        if initlist is not None:
            # XXX should this accept an arbitrary sequence?
            if type(initlist) == type(self.data):
                self.data[:] = initlist
            elif isinstance(initlist, EventedList):
                self.data[:] = initlist.data[:]
            else:
                self.data = list(initlist)

        self.events = self.Events()

    def __repr__(self):
        return repr(self.data)

    def __lt__(self, other):
        return self.data < self.__cast(other)

    def __le__(self, other):
        return self.data <= self.__cast(other)

    def __eq__(self, other):
        return self.data == self.__cast(other)

    def __gt__(self, other):
        return self.data > self.__cast(other)

    def __ge__(self, other):
        return self.data >= self.__cast(other)

    def __cast(self, other):
        return other.data if isinstance(other, EventedList) else other

    def __contains__(self, item):
        return item in self.data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, i):
        if isinstance(i, slice):
            return self.__class__(self.data[i])
        else:
            return self.data[i]

    def __setitem__(self, i, item):
        self.data[i] = item
        self.events.changed.emit()

    def __delitem__(self, i):
        del self.data[i]
        self.events.deleted.emit(i)

    def __add__(self, other):
        if isinstance(other, EventedList):
            return self.__class__(self.data + other.data)
        elif isinstance(other, type(self.data)):
            return self.__class__(self.data + other)
        return self.__class__(self.data + list(other))

    def __radd__(self, other):
        if isinstance(other, EventedList):
            return self.__class__(other.data + self.data)
        elif isinstance(other, type(self.data)):
            return self.__class__(other + self.data)
        return self.__class__(list(other) + self.data)

    def __iadd__(self, other):
        if isinstance(other, EventedList):
            self.data += other.data
        elif isinstance(other, type(self.data)):
            self.data += other
        else:
            self.data += list(other)
        return self

    def __mul__(self, n):
        return self.__class__(self.data * n)

    __rmul__ = __mul__

    def __imul__(self, n):
        self.data *= n
        return self

    def __copy__(self):
        inst = self.__class__.__new__(self.__class__)
        inst.__dict__.update(self.__dict__)
        # Create a copy and avoid triggering descriptors
        inst.__dict__["data"] = self.__dict__["data"][:]
        return inst

    def append(self, item) -> None:
        self.data.append(item)
        self.events.added.emit({"index": len(self.data) - 1, "item": item})

    def insert(self, i, item) -> None:
        self.data.insert(i, item)
        self.events.changed.emit({"index": i, "item": item})

    def pop(self, i: int = -1):
        val = self.data.pop(i)
        self.events.deleted.emit({"index": i, "item": val})
        return val

    def remove(self, item) -> None:
        index = self.index(item)
        self.data.remove(item)
        self.events.deleted.emit(index)

    def clear(self) -> None:
        self.data.clear()
        self.events.changed.emit()

    def copy(self):
        return self.__class__(self)

    def count(self, item):
        return self.data.count(item)

    def index(self, item, *args):
        return self.data.index(item, *args)

    def swap(self, ind1: int, ind2: int):
        (self.data[ind1], self.data[ind2]) = (self.data[ind2], self.data[ind1])
        self.events.swapped.emit({"ind1": ind1, "ind2": ind2})

    def reverse(self) -> None:
        self.data.reverse()
        self.events.changed.emit()

    def sort(self, /, *args, **kwargs) -> None:
        self.data.sort(*args, **kwargs)
        self.events.changed.emit()

    def extend(self, other) -> None:
        if isinstance(other, (EventedList, UserList)):
            self.data.extend(other.data)
        else:
            self.data.extend(other)
        # self.events.changed.emit()


class EventedDict(MutableMapping[T, U]):
    """
    An evented, typed version of built-in dict. Follows the same convention as UserDict.
    """

    class Events:
        def __init__(self):
            self.changed = EventEmitter()

    def __init__(self, *args, **kwargs):
        self.events = self.Events()

        if len(args) > 1:
            raise TypeError(f"expected at most 1 arguments, got {len(args)}")
        if args:
            dct = args[0]
        elif "dict" in kwargs:
            dct = kwargs.pop("dict")
            import warnings

            warnings.warn(
                "Passing 'dict' as keyword argument is deprecated",
                DeprecationWarning,
                stacklevel=2,
            )
        else:
            dct = None
        self.data = {}
        if dct is not None:
            self.update(dct)
        if kwargs:
            self.update(kwargs)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, key):
        if key in self.data:
            return self.data[key]
        if hasattr(self.__class__, "__missing__"):
            return self.__class__.__missing__(self, key)
        raise KeyError(key)

    def __setitem__(self, key, item):
        old_item = self.data.get(key, None)
        if (old_item != item) or (old_item is not item):
            self.data[key] = item
            self.events.changed.emit()

    def __delitem__(self, key):
        del self.data[key]
        self.events.changed.emit()

    def __iter__(self):
        return iter(self.data)

    # Modify __contains__ to work correctly when __missing__ is present
    def __contains__(self, key):
        return key in self.data

    # Now, add the methods in dicts but not in MutableMapping
    def __repr__(self):
        return repr(self.data)

    def __copy__(self):
        inst = self.__class__.__new__(self.__class__)
        inst.__dict__.update(self.__dict__)
        # Create a copy and avoid triggering descriptors
        inst.__dict__["data"] = self.__dict__["data"].copy()
        return inst

    def update(self, m: MutableMapping[T, U], **kwargs) -> None:
        # bulk operation
        self.events.changed.block()
        super().update(m, **kwargs)
        self.events.changed.unblock()
        self.events.changed.emit()

    def clear(self) -> None:
        # bulk operation
        self.events.changed.block()
        super().clear()
        self.events.changed.unblock()
        self.events.changed.emit()

    def copy(self):
        if self.__class__ is EventedDict:
            return EventedDict(self.data.copy())
        import copy

        data = self.data
        try:
            self.data = {}
            c = copy.copy(self)
        finally:
            self.data = data
        c.update(self)
        return c

    @classmethod
    def fromkeys(cls, iterable, value=None):
        d = cls()
        for key in iterable:
            d[key] = value
        return d


class EventedPointF(PointF):
    class Events:
        def __init__(self):
            self.x = EventEmitter()
            self.y = EventEmitter()

    def __init__(self, *args, **kwargs):
        self.events = self.Events()
        super().__init__(*args, **kwargs)

    @property
    def x(self) -> Optional[float]:
        return self._x

    @x.setter
    def x(self, val: Optional[float]) -> None:
        new_val = float(val) if val is not None else None
        if self.x != new_val:
            self._x = new_val
            self.events.x.emit(new_val)

    @property
    def y(self) -> Optional[float]:
        return self._y

    @y.setter
    def y(self, val: Optional[float]) -> None:
        new_val = float(val) if val is not None else None
        if self.y != new_val:
            self._y = new_val
            self.events.y.emit(new_val)

    def __repr__(self) -> str:
        return f"EventedPointF(x={self.x}, y={self.y})"


class EventedPoint:
    class Events:
        def __init__(self):
            self.x = EventEmitter()
            self.y = EventEmitter()

    def __init__(self, /, x: Optional[int] = None, y: Optional[int] = None):
        self.events = self.Events()
        self._x = x
        self._y = y

    @property
    def x(self) -> Optional[int]:
        return self._x

    @x.setter
    def x(self, val: Optional[float]) -> None:
        new_val = int(val) if val is not None else None
        if self.x != new_val:
            self._x = new_val
            self.events.x.emit(new_val)

    @property
    def y(self) -> Optional[int]:
        return self._y

    @y.setter
    def y(self, val: Optional[float]) -> None:
        new_val = int(val) if val is not None else None
        if self.y != new_val:
            self._y = new_val
            self.events.y.emit(new_val)

    def is_valid(self) -> bool:
        return (self.x is not None) and (self.y is not None)

    def __repr__(self) -> str:
        return f"Point(x={self.x}, y={self.y})"

    def as_tuple(self) -> Tuple[Optional[int], Optional[int]]:
        return (self.x, self.y)


class EventedAngle(Angle):
    """
    Angle, [0, 2pi).
    On the view side, we use degrees; internally, we use radians.
    """

    class Events:
        def __init__(self):
            self.value = EventEmitter()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.events = self.Events()

    @property
    def rad(self) -> float:
        return self._val

    @rad.setter
    def rad(self, val: float) -> None:
        # all angle-setting goes through here
        new_val = clip_angle(val)
        if hasattr(self, "_val"):
            if self._val != new_val:
                self._val = new_val
                self.events.value.emit(self)
        else:
            # initial value set
            self._val = new_val

    def __repr__(self) -> str:
        return f"EventedAngle({self.rad})"
