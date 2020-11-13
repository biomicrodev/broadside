from PySide2.QtWidgets import QWidget, QLabel, QVBoxLayout

from broadside.gui.components.panel import BasePanel


class ProjectWidget(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)

        label = QLabel()
        label.setText("Project panel")

        layout = QVBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)


class ProjectPanel(BasePanel):
    name = "Project"

    def __init__(self, *args, parent: QWidget = None, **kwargs):
        super().__init__(*args, **kwargs)

        self.view = ProjectWidget(parent=parent)
