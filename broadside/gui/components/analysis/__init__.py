import logging

from .view import AnalysisView
from ..editor import Editor
from ...models.project import ProjectModel


class AnalysisEditor(Editor):
    log = logging.getLogger(__name__)

    name = "Analysis"

    def __init__(self, model: ProjectModel, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.model = model
        self.view = AnalysisView()
