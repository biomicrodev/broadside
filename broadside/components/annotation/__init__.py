import logging

from .view import AnnotationView
from ..editor import Editor
from ..viewermodel import ViewerModel


class AnnotationEditor(Editor):
    log = logging.getLogger(__name__)

    name = "Annotation"

    def __init__(self, model: ViewerModel, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.model = model
        self.view = AnnotationView()
