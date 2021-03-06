from enum import Enum


class Color(Enum):
    White = (255, 255, 255)
    Gray = (170, 170, 170)
    Black = (0, 0, 0)

    Red = (130, 30, 30)
    Green = (30, 130, 30)
    Blue = (30, 30, 130)

    def css(self) -> str:
        return f'rgb({", ".join([str(v) for v in self.value])})'
