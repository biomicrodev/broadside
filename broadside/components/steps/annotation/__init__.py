import logging

from qtpy.QtWidgets import QLabel

from .. import Step
from ...viewer_model import ViewerModel


class AnnotationStep(Step):
    log = logging.getLogger(__name__)

    name = "Annotation"

    def __init__(self, model: ViewerModel):
        super().__init__()

        self._view = QLabel("annotation")
        # self._view = AnnotationView(model)
