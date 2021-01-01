from dataclasses import dataclass
from typing import Any, Dict, List

from .serializable import Serializable


@dataclass
class Channel(Serializable):
    keys = ["biomarker", "chromatic", "notes"]
    headers = ["Biomarker", "Chromatic", "Notes"]

    biomarker: str
    chromatic: str
    notes: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "biomarker": self.biomarker,
            "chromatic": self.chromatic,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]):
        biomarker = dct.get("biomarker", "")
        chromatic = dct.get("chromatic", "")
        notes = dct.get("notes", "")

        return cls(biomarker=biomarker, chromatic=chromatic, notes=notes)


@dataclass
class Panel(Serializable):
    name: str
    channels: List[Channel]

    def as_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "channels": [c.as_dict() for c in self.channels]}

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]):
        name = dct.get("name", "Unnamed")

        channels = dct.get("channels", [])
        channels = [Channel.from_dict(c) for c in channels]

        return cls(name=name, channels=channels)
