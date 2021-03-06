import logging

from qtpy.QtWidgets import QLabel

from .view import AnalysisView
from .. import Step
from ...viewer_model import ViewerModel


class AnalysisStep(Step):
    log = logging.getLogger(__name__)

    name = "Analysis"

    def __init__(self, model: ViewerModel):
        super().__init__()

        self._view = QLabel("analysis")

        # self.model = model
        # self.view = AnalysisView()
