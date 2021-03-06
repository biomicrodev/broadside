from qtpy.QtWidgets import QLabel

from ....editor import Editor
from ....viewer_model import ViewerModel


class ImagesEditor(Editor):
    def __init__(self, model: ViewerModel):
        super().__init__()

        self.model = model
        self._view = QLabel("Images")
