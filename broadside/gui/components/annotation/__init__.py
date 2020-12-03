import logging

from .view import AnnotationView
from ..editor import BaseEditor


class AnnotationEditor(BaseEditor):
    log = logging.getLogger(__name__)

    name = "Annotation"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.view = AnnotationView()

    def beforeDelete(self) -> None:
        pass
