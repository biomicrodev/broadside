from PySide2.QtWidgets import QWidget, QLabel, QVBoxLayout


class AnnotationView(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        label = QLabel()
        label.setText("Annotation editor")

        layout = QVBoxLayout()
        layout.addWidget(label)

        self.setLayout(layout)
