from dataclasses import dataclass
from typing import Dict, Any, List

from . import Serializable


class Sample(Serializable):
    keys = ["name", "deviceName"]
    headers = ["Name", "Device name"]
    types = [str, str]

    def __init__(
        self, *, name: str = "", deviceName: str = "", cohorts: Dict[str, str] = None
    ):
        self._name = name
        self._deviceName = deviceName
        self._cohorts = cohorts or {}

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, val: str) -> None:
        self._name = val

    @property
    def deviceName(self) -> str:
        return self._deviceName

    @deviceName.setter
    def deviceName(self, val: str) -> None:
        self._deviceName = val

    @property
    def cohorts(self) -> Dict[str, str]:
        return self._cohorts

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "device_name": self.deviceName,
            "cohorts": self.cohorts,
        }

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]):
        name = dct.get("name", "")
        deviceName = dct.get("device_name", "")
        cohorts = dct.get("cohorts", {})

        return cls(name=name, deviceName=deviceName, cohorts=cohorts)


@dataclass
class SampleIndicator(Serializable):
    pass


@dataclass
class SampleGroup(Serializable):
    name: str
    cohorts: List[str]
    samples: List[Sample]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "cohorts": self.cohorts,
            "samples": self.samples,
        }

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]):
        name = dct.get("name", "Unnamed")
        cohorts = dct.get("cohorts", [])
        samples = dct.get("samples", [])
        samples = [Sample.from_dict(s) for s in samples]

        return cls(name=name, cohorts=cohorts, samples=samples)
