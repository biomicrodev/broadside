from typing import Any, Dict, List, Optional

from ..utils.events import EventEmitter, EventedList
from ..utils.serializable import Serializable


class Channel(Serializable):
    keys = ["biomarker", "chromogen", "notes"]
    headers = ["Biomarker", "Chromogen", "Notes"]
    types = [str, str, str]

    class Events:
        def __init__(self):
            self.biomarker = EventEmitter()
            self.chromogen = EventEmitter()
            self.notes = EventEmitter()

    def __init__(self, *, biomarker: str = "", chromogen: str = "", notes: str = ""):
        self.events = self.Events()

        self._biomarker = biomarker
        self._chromogen = chromogen
        self._notes = notes

    @property
    def biomarker(self) -> str:
        return self._biomarker

    @biomarker.setter
    def biomarker(self, val: str) -> None:
        if self.biomarker != val:
            self._biomarker = val
            self.events.biomarker.emit(val)

    @property
    def chromogen(self) -> str:
        return self._chromogen

    @chromogen.setter
    def chromogen(self, val: str) -> None:
        if self.chromogen != val:
            self._chromogen = val
            self.events.chromogen.emit(val)

    @property
    def notes(self) -> str:
        return self._notes

    @notes.setter
    def notes(self, val: str) -> None:
        if self.notes != val:
            self._notes = val
            self.events.notes.emit(val)

    def is_valid(self) -> bool:
        return self.biomarker != ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "biomarker": self.biomarker,
            "chromogen": self.chromogen,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]) -> "Channel":
        biomarker = dct.get("biomarker", "")
        chromogen = dct.get("chromogen", "")
        notes = dct.get("notes", "")

        return cls(biomarker=biomarker, chromogen=chromogen, notes=notes)

    def __repr__(self) -> str:
        return (
            "Channel("
            f"biomarker={self.biomarker}, "
            f"chromogen={self.chromogen}, "
            f"notes={self.notes}"
            ")"
        )


class Panel(Serializable):
    class Events:
        def __init__(self):
            self.name = EventEmitter()

    def __init__(self, *, name: str = "", channels: Optional[List[Channel]] = None):
        self.events = self.Events()

        self._name = name
        self._channels = EventedList(channels if channels is not None else [])

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, val: str) -> None:
        if self.name != val:
            self._name = val
            self.events.name.emit(val)

    @property
    def channels(self) -> EventedList[Channel]:
        return self._channels

    def is_valid(self) -> bool:
        return (self.name != "") and all(c.is_valid() for c in self.channels)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "channels": [c.as_dict() for c in self.channels],
        }

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]) -> "Panel":
        name = dct.get("name", "")

        channels = dct.get("channels", [])
        channels = [Channel.from_dict(c) for c in channels]

        return cls(name=name, channels=channels)

    def __repr__(self) -> str:
        return f"Panel(name={self.name}, channel={self.channels})"
