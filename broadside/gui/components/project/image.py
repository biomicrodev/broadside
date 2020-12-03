from PySide2.QtWidgets import QWidget, QVBoxLayout, QLabel


class ImageListEditorView(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        label = QLabel()
        label.setText("Image list editor")

        layout = QVBoxLayout()
        layout.addWidget(label)

        self.setLayout(layout)


class ImageListEditor:
    def __init__(self):
        self.view = ImageListEditorView()
