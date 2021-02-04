from qtpy.QtWidgets import QWidget, QLabel, QVBoxLayout


class AnalysisView(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        label = QLabel()
        label.setText("Analysis editor")

        layout = QVBoxLayout()
        layout.addWidget(label)

        self.setLayout(layout)
