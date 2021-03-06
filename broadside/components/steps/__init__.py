from typing import Optional

from qtpy.QtWidgets import QWidget

from ...utils.validatable import Validatable


class Step(Validatable):
    name = ""

    def __init__(self):
        super().__init__()

        self._view: Optional[QWidget] = None
