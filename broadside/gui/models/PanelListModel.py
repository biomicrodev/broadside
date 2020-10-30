from PySide2.QtCore import QAbstractListModel


class PanelListModel(QAbstractListModel):
    def __init__(self, parent):
        super().__init__(parent)
