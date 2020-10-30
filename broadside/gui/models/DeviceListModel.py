from PySide2.QtCore import QAbstractListModel


class DeviceListModel(QAbstractListModel):
    def __init__(self, parent):
        super().__init__(parent)
