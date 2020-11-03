from PySide2.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel, QScrollArea


class DevicesWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setUpUI()

    def setUpUI(self):
        tab1 = QLabel()
        tab1.setText("test")

        tabWidget = QTabWidget()
        tabWidget.setTabsClosable(True)
        tabWidget.addTab(tab1, "test tab")

        innerLayout = QVBoxLayout()
        innerLayout.addWidget(tabWidget)

        scrollArea = QScrollArea()
        scrollArea.setLayout(innerLayout)

        layout = QVBoxLayout()
        layout.addWidget(scrollArea)
        self.setLayout(layout)
