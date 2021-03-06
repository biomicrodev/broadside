from enum import Enum
from typing import Dict, Any, Optional, List

from ..utils.events import EventEmitter, EventedAngle, EventedList
from ..utils.serializable import Serializable


class Fiducial(Enum):
    Notch = "notch"


class LongOrient(Enum):
    # longitudinal orientation
    TipIntoPage = "tip into page/booster out of page"
    TipOutOfPage = "tip out of page/booster into page"


class LongDir(Enum):
    # longitudinal direction
    IncreasingTowardsTip = "levels increasing towards tip"
    IncreasingTowardsBooster = "levels increasing towards booster"


class AngDir(Enum):
    # angular direction
    Clockwise = "clockwise positive"
    CounterClockwise = "counterclockwise positive"


class Formulation(Serializable):
    keys = ["level", "angle", "name"]
    headers = ["Level", "Angle", "Name"]
    types = [str, float, str]

    class Events:
        def __init__(self):
            self.level = EventEmitter()
            self.name = EventEmitter()

    def __init__(self, *, level: str = "", angle: float = 0.0, name: str = ""):
        self.events = self.Events()

        self._level = level
        self._angle = EventedAngle(deg=angle)
        self._name = name

    @property
    def level(self) -> str:
        return self._level

    @level.setter
    def level(self, val: str) -> None:
        if self.level != val:
            self._level = val
            self.events.level.emit(val)

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, val: str) -> None:
        if self.name != val:
            self._name = val
            self.events.name.emit(val)

    @property
    def angle(self) -> EventedAngle:
        return self._angle

    def is_valid(self) -> bool:
        return (self.level != "") and (self.name != "")

    def as_dict(self) -> Dict[str, Any]:
        return {"level": self.level, "angle": self.angle.int, "name": self.name}

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]) -> "Formulation":
        level = dct.get("level", "")

        angle = dct.get("angle", 0.0)
        angle = float(angle)

        name = dct.get("name", "")

        return cls(level=level, angle=angle, name=name)

    def __repr__(self) -> str:
        return f"Formulation(level={self.level}, angle={self.angle}, name={self.name})"


class Payload(Serializable):
    class Events:
        def __init__(self):
            self.name = EventEmitter()
            self.long_orient = EventEmitter()
            self.long_dir = EventEmitter()
            self.ang_dir = EventEmitter()
            self.notes = EventEmitter()

    def __init__(
        self,
        name: str = "",
        long_orient: Optional[LongOrient] = None,
        long_dir: Optional[LongDir] = None,
        ang_dir: Optional[AngDir] = None,
        formulations: Optional[List[Formulation]] = None,
        notes: str = "",
    ):
        self.events = self.Events()

        self._name = name
        self._long_orient = long_orient
        self._long_dir = long_dir
        self._ang_dir = ang_dir
        self._formulations = EventedList(
            formulations if formulations is not None else []
        )
        self._notes = notes

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
    def long_orient(self) -> Optional[LongOrient]:
        return self._long_orient

    @long_orient.setter
    def long_orient(self, val: LongOrient) -> None:
        if self.long_orient != val:
            self._long_orient = val
            self.events.long_orient.emit(val)

    @property
    def long_dir(self) -> Optional[LongDir]:
        return self._long_dir

    @long_dir.setter
    def long_dir(self, val: LongDir) -> None:
        if self.long_dir != val:
            self._long_dir = val
            self.events.long_dir.emit(val)

    @property
    def ang_dir(self) -> Optional[AngDir]:
        return self._ang_dir

    @ang_dir.setter
    def ang_dir(self, val: AngDir) -> None:
        if self.ang_dir != val:
            self._ang_dir = val
            self.events.ang_dir.emit(val)

    @property
    def formulations(self) -> EventedList[Formulation]:
        return self._formulations

    @property
    def notes(self) -> str:
        return self._notes

    @notes.setter
    def notes(self, val: str) -> None:
        if self.notes != val:
            self._notes = val
            self.events.notes.emit(val)

    def is_formulations_unique(self) -> bool:
        levels_angles = [(f.level, f.angle) for f in self.formulations]
        levels_angles_as_set = set(levels_angles)
        return len(levels_angles) == len(levels_angles_as_set)

    def is_valid(self) -> bool:
        return (
            (self.name != "")
            and (self.long_orient is not None)
            and (self.long_dir is not None)
            and (self.ang_dir is not None)
            and all(f.is_valid() for f in self.formulations)
            and self.is_formulations_unique()
        )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "longitudinal_orientation": self.long_orient.value,
            "longitudinal_direction": self.long_dir.value,
            "angular_direction": self.ang_dir.value,
            "formulations": [f.as_dict() for f in self.formulations],
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, dct: Dict[str, Any]) -> "Payload":
        name = dct.get("name", "Unnamed")

        long_orient = dct.get("longitudinal_orientation", None)
        long_orient = LongOrient(long_orient) if long_orient is not None else None

        long_dir = dct.get("longitudinal_direction", None)
        long_dir = LongDir(long_dir) if long_dir is not None else None

        ang_dir = dct.get("angular_direction", None)
        ang_dir = AngDir(ang_dir) if ang_dir is not None else None

        formulations = dct.get("formulations", [])
        formulations = [Formulation.from_dict(f) for f in formulations]

        notes = dct.get("notes", "")

        return cls(
            name=name,
            long_orient=long_orient,
            long_dir=long_dir,
            ang_dir=ang_dir,
            formulations=formulations,
            notes=notes,
        )

    def __repr__(self) -> str:
        return (
            "Payload("
            f"name={self.name}, "
            f"longitudinal_orientation={self.long_orient}, "
            f"longitudinal_direction={self.long_dir}, "
            f"angular_direction={self.ang_dir}, "
            f"formulations={self.formulations}, "
            f"notes={self.notes}"
            ")"
        )
