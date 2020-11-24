from typing import List, Optional

from PySide2.QtCore import Qt
from PySide2.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QHBoxLayout,
    QPushButton,
    QMessageBox,
    QLabel,
    QLineEdit,
    QComboBox,
    QGridLayout,
    QScrollArea,
    QAbstractScrollArea,
)

from broadside.gui.components.project.payload import PayloadWidget
from broadside.gui.models.device import (
    LongitudinalOrientation,
    LongitudinalDirection,
    AngularDirection,
    Device,
)
from broadside.gui.utils import showDeleteDialog, QStaleableObject


class DeviceWidget(QWidget, QStaleableObject):
    def __init__(
        self, *args, device: Optional[Device] = None, _init_name: str = "", **kwargs
    ):
        super().__init__(*args, **kwargs)

        self._device = device
        self._init_name = _init_name

        self.setUpUI()

    def setUpUI(self):
        nameLabel = QLabel("Name:")
        nameLabelEdit = QLineEdit(self._init_name)
        nameLabel.setBuddy(nameLabelEdit)
        self.nameLabelEdit = nameLabelEdit

        longOrientLabel = QLabel("Longitudinal orientation:")
        longOrientComboBox = QComboBox()
        longOrientComboBox.insertItems(
            0,
            [
                LongitudinalOrientation.TipIntoPage.value,
                LongitudinalOrientation.TipOutOfPage.value,
            ],
        )
        longOrientLabel.setBuddy(longOrientComboBox)
        self.longitudinalOrientationComboBox = longOrientComboBox

        longDirLabel = QLabel("Longitudinal direction:")
        longDirComboBox = QComboBox()
        longDirComboBox.insertItems(
            0,
            [
                LongitudinalDirection.IncreasingTowardsTip.value,
                LongitudinalDirection.IncreasingTowardsBooster.value,
            ],
        )
        longDirLabel.setBuddy(longDirComboBox)
        self.longitudinalDirectionComboBox = longDirComboBox

        angDirLabel = QLabel("Angular direction:")
        angDirComboBox = QComboBox()
        angDirComboBox.insertItems(
            0,
            [AngularDirection.Clockwise.value, AngularDirection.CounterClockwise.value],
        )
        angDirComboBox.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        angDirLabel.setBuddy(angDirComboBox)
        self.angularDirectionComboBox = angDirComboBox

        payloadWidget = PayloadWidget()
        # payloadWidget.setMaximumWidth(500)
        payloadWidget.setMinimumHeight(400)
        self.payloadWidget = payloadWidget

        layout = QGridLayout()
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 1)
        layout.setColumnMinimumWidth(0, 200)
        layout.setColumnMinimumWidth(1, 200)

        layout.addWidget(nameLabel, 0, 0, Qt.AlignRight)
        layout.addWidget(nameLabelEdit, 0, 1, Qt.AlignLeft)
        layout.setRowStretch(0, 1)

        layout.addWidget(longOrientLabel, 1, 0, Qt.AlignRight)
        layout.addWidget(longOrientComboBox, 1, 1, Qt.AlignLeft)
        layout.setRowStretch(1, 1)

        layout.addWidget(longDirLabel, 2, 0, Qt.AlignRight)
        layout.addWidget(longDirComboBox, 2, 1, Qt.AlignLeft)
        layout.setRowStretch(2, 1)

        layout.addWidget(angDirLabel, 3, 0, Qt.AlignRight)
        layout.addWidget(angDirComboBox, 3, 1, Qt.AlignLeft)
        layout.setRowStretch(3, 1)

        layout.addWidget(payloadWidget, 4, 0, 1, 2)
        layout.setRowStretch(4, 1)

        layout.addWidget(QWidget(), 5, 0)
        layout.setRowStretch(5, 1)

        parentWidget = QWidget()
        parentWidget.setLayout(layout)

        scrollArea = QScrollArea()
        scrollArea.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        scrollArea.setWidget(parentWidget)
        containerLayout = QVBoxLayout()
        containerLayout.addWidget(scrollArea)
        self.setLayout(containerLayout)


class DeviceListWidget(QWidget):
    def __init__(self, devices: List[Device] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._devices = devices or []

        self.setUpUI()
        self.setUpReactivity()

    def setUpUI(self):
        deviceTabWidget = QTabWidget()
        deviceTabWidget.setMovable(True)
        self.tabWidget = deviceTabWidget

        addDeviceButton = QPushButton()
        addDeviceButton.setText("Add device")
        self.addDeviceButton = addDeviceButton

        deleteDeviceButton = QPushButton()
        deleteDeviceButton.setObjectName("DeleteDeviceButton")
        deleteDeviceButton.setText("Delete device")
        deleteDeviceButton.setStyleSheet(
            """\
QPushButton#DeleteDeviceButton {
    background-color: rgb(190, 30, 30);
}
QPushButton#DeleteDeviceButton:enabled {
    color: white;
}
        """
        )
        self.deleteDeviceButton = deleteDeviceButton
        self._updateDeleteButton()

        buttonsLayout = QHBoxLayout()
        buttonsLayout.addStretch(1)
        buttonsLayout.addWidget(addDeviceButton)
        buttonsLayout.addWidget(deleteDeviceButton)

        layout = QVBoxLayout()
        layout.addWidget(deviceTabWidget)
        layout.addLayout(buttonsLayout)
        self.setLayout(layout)

    def _updateDeleteButton(self):
        self.deleteDeviceButton.setEnabled(self.tabWidget.count() >= 2)

    def setUpReactivity(self):
        def addNewDevice():
            nWidgets = self.tabWidget.count()
            name = f"New device {str(nWidgets + 1)}"

            widget = DeviceWidget(_init_name=name)
            self.tabWidget.addTab(widget, name)

            def updateTabText(name: str) -> None:
                index = self.tabWidget.indexOf(widget)
                self.tabWidget.setTabText(index, name)

            widget.nameLabelEdit.textChanged.connect(lambda name: updateTabText(name))

            index = self.tabWidget.indexOf(widget)
            self.tabWidget.setCurrentIndex(index)

            self._updateDeleteButton()

        self.addDeviceButton.clicked.connect(lambda: addNewDevice())

        def deleteDevice():
            index = self.tabWidget.currentIndex()
            name = self.tabWidget.tabText(index)

            response = showDeleteDialog(
                title=f"Delete {name}?", text=f"Are you sure you want to delete {name}?"
            )
            if response == QMessageBox.Yes:
                self.tabWidget.removeTab(index)

                self._updateDeleteButton()

        self.deleteDeviceButton.clicked.connect(lambda: deleteDevice())


if __name__ == "__main__":
    import sys
    from PySide2.QtWidgets import QApplication

    app = QApplication()
    widget = DeviceListWidget()
    widget.show()
    sys.exit(app.exec_())
