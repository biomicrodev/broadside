import sys
from typing import List

from PySide2.QtWidgets import QTabWidget, QMainWindow, QApplication


class Block:
    pass


class BlockTabWidget(QTabWidget):
    def __init__(self, *args, blocks: List[Block] = None, **kwargs):
        super().__init__(*args, **kwargs)

        self.blocks = blocks or []

        self.setTabsClosable(True)
        self.setMovable(True)


if __name__ == "__main__":
    app = QApplication()

    tabWidget = BlockTabWidget()

    window = QMainWindow()
    window.setCentralWidget(tabWidget)
    window.show()

    sys.exit(app.exec_())
