import logging

from .view import AnalysisView
from ..editor import BaseEditor


class AnalysisEditor(BaseEditor):
    log = logging.getLogger(__name__)

    name = "Analysis"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.view = AnalysisView()

    def beforeDelete(self) -> None:
        pass
