from typing import Dict, Any, Optional, List

from ..utils.events import (
    EventedList,
    EventedDict,
    EventEmitter,
    EventedPoint,
    EventedAngle,
)
from ..utils.serializable import Serializable


class Vector(Serializable):
    """
    The angle is serialized in integer degrees for human-readability.
    """

    def __init__(self, *, pos: Optional[EventedPoint] = None, angle: float = 0.0):
        self._pos: EventedPoint = pos if pos is not None else EventedPoint()
        self._angle = EventedAngle(deg=angle)

    @property
    def pos(self) -> EventedPoint:
        return self._pos

    @property
    def angle(self) -> EventedAngle:
        return self._angle

    def is_valid(self) -> bool:
        return (self.pos is not None) and (self.pos.is_valid())

    def as_dict(self) -> Dict[str, Any]:
        return {
            "pos": (self.pos.x, self.pos.y),
            "angle": self.angle.int,
        }

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]) -> "Vector":
        pos = dct.get("pos", None)
        pos = EventedPoint(*(pos[:2])) if (pos is not None) else EventedPoint()

        angle = dct.get("angle", 0)
        angle = float(angle)

        return cls(pos=pos, angle=angle)

    def __repr__(self) -> str:
        return f"Vector(pos={self.pos}, angle={self.angle})"


class Sample(Serializable):
    keys = ["name"]
    headers = ["Name"]
    types = [str]

    class Events:
        def __init__(self):
            self.name = EventEmitter()

    def __init__(self, *, name: str = "", cohorts: Optional[Dict[str, str]] = None):
        self.events = self.Events()

        self._name = name
        self._cohorts = EventedDict(cohorts if cohorts is not None else {})

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, val: str) -> None:
        if self.name != val:
            old_val = self.name
            self._name = val
            self.events.name.emit({"old": old_val, "new": val})

    @property
    def cohorts(self) -> EventedDict:
        return self._cohorts

    def is_valid(self) -> bool:
        return self.name != ""  # and self.vector.is_valid()

    def as_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "cohorts": dict(self.cohorts)}

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]) -> "Sample":
        name = dct.get("name", "")
        cohorts = dct.get("cohorts", {})
        return cls(name=name, cohorts=cohorts)

    def __repr__(self) -> str:
        return f"Sample(name={self.name}, cohorts={self.cohorts})"


class Device(Serializable):
    keys = ["name", "payload_name", "sample_name"]
    headers = ["Name", "Payload name", "Sample name"]
    types = [str, str, str]

    class Events:
        def __init__(self):
            self.name = EventEmitter()
            self.payload_name = EventEmitter()
            self.sample_name = EventEmitter()

    def __init__(
        self, *, name: str = "", payload_name: str = "", sample_name: str = ""
    ):
        self.events = self.Events()

        self._name = name
        self._payload_name = payload_name
        self._sample_name = sample_name

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, val: str) -> None:
        if self.name != val:
            self._name = val
            self.events.name.emit(val)

    @property
    def payload_name(self) -> str:
        return self._payload_name

    @payload_name.setter
    def payload_name(self, val: str) -> None:
        if self.payload_name != val:
            self._payload_name = val
            self.events.payload_name.emit(val)

    @property
    def sample_name(self) -> str:
        return self._sample_name

    @sample_name.setter
    def sample_name(self, val: str) -> None:
        if self.sample_name != val:
            self._sample_name = val
            self.events.sample_name.emit(val)

    def is_valid(self) -> bool:
        return (
            (self.name != "") and (self.payload_name != "") and (self.sample_name != "")
        )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "payload_name": self.payload_name,
            "sample_name": self.sample_name,
        }

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]) -> "Device":
        name = dct.get("name", "")
        payload_name = dct.get("payload_name", "")
        sample_name = dct.get("sample_name", "")
        return cls(name=name, payload_name=payload_name, sample_name=sample_name)

    def __repr__(self):
        return (
            "Device("
            f"name={self.name}, "
            f"payload_name={self.payload_name}, "
            f"sample_name={self._sample_name}"
            ")"
        )


class Block(Serializable):
    class Events:
        def __init__(self):
            self.name = EventEmitter()
            self.notes = EventEmitter()

    def __init__(
        self,
        *,
        name: str = "",
        samples: Optional[List[Sample]] = None,
        devices: Optional[List[Device]] = None,
        vectors: Optional[List[Vector]] = None,
        notes: str = "",
    ):
        self.events = self.Events()

        self._name = name
        self._samples = EventedList(samples if samples is not None else [])
        self._devices = EventedList(devices if devices is not None else [])
        self._vectors = EventedList(vectors if vectors is not None else [])
        self._notes = notes

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, val: str) -> None:
        if self.name != val:
            self._name = val
            self.events.name.emit(val)

    @property
    def samples(self) -> EventedList[Sample]:
        return self._samples

    @property
    def devices(self) -> EventedList[Device]:
        return self._devices

    @property
    def vectors(self) -> EventedList[Vector]:
        return self._vectors

    @property
    def notes(self) -> str:
        return self._notes

    @notes.setter
    def notes(self, val: str) -> None:
        if self.notes != val:
            self._notes = val
            self.events.notes.emit(val)

    def is_valid(self) -> bool:
        return (
            (self.name != "")
            and all(s.is_valid() for s in self.samples)
            and all(d.is_valid() for d in self.devices)
        )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "samples": [s.as_dict() for s in self.samples],
            "devices": [d.as_dict() for d in self.devices],
            "vectors": [v.as_dict() for v in self.vectors],
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]) -> "Block":
        name = dct.get("name", "")

        samples = dct.get("samples", [])
        samples = [Sample.from_dict(s) for s in samples]

        devices = dct.get("devices", [])
        devices = [Device.from_dict(d) for d in devices]

        vectors = dct.get("vectors", [])
        vectors = [Vector.from_dict(v) for v in vectors]

        notes = dct.get("notes", "")

        return cls(
            name=name, samples=samples, devices=devices, vectors=vectors, notes=notes
        )

    def __repr__(self) -> str:
        return (
            "Block("
            f"name={self.name}, "
            f"samples={self.samples}, "
            f"devices={self.devices}, "
            f"vectors={self.vectors}, "
            f"notes={self.notes}"
            ")"
        )
