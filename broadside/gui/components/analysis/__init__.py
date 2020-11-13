from PySide2.QtWidgets import QWidget, QLabel, QVBoxLayout

from broadside.gui.components.panel import BasePanel


class AnalysisWidget(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)

        label = QLabel()
        label.setText("Analysis panel")

        layout = QVBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)


class AnalysisPanel(BasePanel):
    name = "Analysis"

    def __init__(self, *args, parent: QWidget = None, **kwargs):
        super().__init__(*args, **kwargs)

        self.view = AnalysisWidget(parent=parent)
