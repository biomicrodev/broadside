from dataclasses import dataclass, field
from typing import Any, Dict, List

from .serializable import Serializable


@dataclass
class Channel(Serializable):
    keys = ["biomarker", "chromogen", "notes"]
    headers = ["Biomarker", "Chromogen", "Notes"]

    biomarker: str = ""
    chromogen: str = ""
    notes: str = ""

    def is_valid(self) -> bool:
        return self.biomarker != ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "biomarker": self.biomarker,
            "chromogen": self.chromogen,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]):
        biomarker = dct.get("biomarker", "")
        chromogen = dct.get("chromogen", "")
        notes = dct.get("notes", "")

        return cls(biomarker=biomarker, chromogen=chromogen, notes=notes)


@dataclass
class Panel(Serializable):
    name: str = ""
    channels: List[Channel] = field(default_factory=list)

    def is_valid(self) -> bool:
        return (self.name != "") and all(c.is_valid() for c in self.channels)

    def as_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "channels": [c.as_dict() for c in self.channels]}

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]) -> "Panel":
        name = dct.get("name", "")

        channels = dct.get("channels", [])
        channels = [Channel.from_dict(c) for c in channels]

        return cls(name=name, channels=channels)
