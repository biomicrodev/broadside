import logging

from .view import AnnotationView
from ..editor import Editor
from ..session import Session


class AnnotationEditor(Editor):
    log = logging.getLogger(__name__)

    name = "Annotation"

    def __init__(self, model: Session, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.model = model
        self.view = AnnotationView()
