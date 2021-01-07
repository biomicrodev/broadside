from dataclasses import dataclass
from typing import Dict, Any

from .serializable import Serializable


@dataclass
class TaskGraph(Serializable):
    def is_valid(self) -> bool:
        return True

    def as_dict(self) -> Dict[str, Any]:
        return {}

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]) -> "TaskGraph":
        return cls()

    def __repr__(self) -> str:
        return f"TaskGraph()"
