from dataclasses import dataclass
from typing import Dict, Any

from .serializable import Serializable


@dataclass
class TaskGraph(Serializable):
    def as_dict(self) -> Dict[str, Any]:
        return {}

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]):
        return cls()
