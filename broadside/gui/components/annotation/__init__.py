from PySide2.QtWidgets import QWidget, QVBoxLayout, QLabel

from ..panel import BasePanel
from ...models.project import ProjectModel


class AnnotationWidget(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)

        label = QLabel()
        label.setText("Annotation panel")

        layout = QVBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)


class AnnotationPanel(BasePanel):
    name = "Annotation"

    def __init__(self, *args, model: ProjectModel, parent: QWidget = None, **kwargs):
        super().__init__(*args, **kwargs)

        self.model = model
        self.view = AnnotationWidget(parent=parent)
