import logging

from .view import AnalysisView
from ..editor import Editor
from ..viewermodel import ViewerModel


class AnalysisEditor(Editor):
    log = logging.getLogger(__name__)

    name = "Analysis"

    def __init__(self, model: ViewerModel, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.model = model
        self.view = AnalysisView()
