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
)

from broadside.gui.components.project.payload import PayloadWidget
from broadside.gui.models.device import (
    LongitudinalDirection,
    AngularDirection,
    Device,
    LongitudinalOrdinality,
)


class DeviceWidget(QWidget):
    def __init__(
        self, *args, device: Optional[Device] = None, _init_name: str = "", **kwargs
    ):
        super().__init__(*args, **kwargs)

        self._device = device
        self._init_name = _init_name

        self.setUpUI()
        self.setUpReactivity()

    def setUpUI(self):
        nameLabel = QLabel("Name:")
        nameLabelEdit = QLineEdit(self._init_name)
        nameLabel.setBuddy(nameLabelEdit)
        self.nameLabelEdit = nameLabelEdit

        longDirLabel = QLabel("Longitudinal direction:")
        longDirComboBox = QComboBox()
        longDirComboBox.insertItems(
            0,
            [
                LongitudinalDirection.TipIntoScreen.value,
                LongitudinalDirection.TipOutOfScreen.value,
            ],
        )
        longDirLabel.setBuddy(longDirComboBox)
        self.longitudinalDirectionComboBox = longDirComboBox

        longOrdLabel = QLabel("Longitudinal ordinality:")
        longOrdComboBox = QComboBox()
        longOrdComboBox.insertItems(
            0,
            [
                LongitudinalOrdinality.IncreasingTowardsTip.value,
                LongitudinalOrdinality.IncreasingTowardsBooster.value,
            ],
        )
        longOrdLabel.setBuddy(longOrdComboBox)
        self.longitudinalOrdinalityComboBox = longOrdComboBox

        angDirLabel = QLabel("Angular direction:")
        angDirComboBox = QComboBox()
        angDirComboBox.insertItems(
            0,
            [AngularDirection.Clockwise.value, AngularDirection.Counterclockwise.value],
        )
        angDirComboBox.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        angDirLabel.setBuddy(angDirComboBox)
        self.angularDirectionComboBox = angDirComboBox

        payloadWidget = PayloadWidget()
        payloadWidget.setMaximumWidth(500)
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

        layout.addWidget(longDirLabel, 1, 0, Qt.AlignRight)
        layout.addWidget(longDirComboBox, 1, 1, Qt.AlignLeft)
        layout.setRowStretch(1, 1)

        layout.addWidget(longOrdLabel, 2, 0, Qt.AlignRight)
        layout.addWidget(longOrdComboBox, 2, 1, Qt.AlignLeft)
        layout.setRowStretch(3, 1)

        layout.addWidget(angDirLabel, 3, 0, Qt.AlignRight)
        layout.addWidget(angDirComboBox, 3, 1, Qt.AlignLeft)
        layout.setRowStretch(3, 1)

        layout.addWidget(payloadWidget, 4, 0, 1, 2)
        layout.setRowStretch(4, 1)

        layout.addWidget(QWidget(), 5, 0)
        layout.setRowStretch(5, 1)

        self.setLayout(layout)

    # def setUpReactivity(self):
    #     def updateFiducialComboBox():
    #         fiducial = self.fiducialComboBox.currentText()
    #
    #         formulations = self.payloadWidget.model.formulations
    #         formulations = ["Notch"] + [
    #             f"{f.level}, {f.angle}, {f.name}" for f in formulations
    #         ]
    #         self.fiducialComboBox.clear()
    #
    #         self.fiducialComboBox.insertItems(0, formulations)
    #         if fiducial in formulations:
    #             self.fiducialComboBox.setCurrentText(fiducial)
    #
    #     self.payloadWidget.model.layoutChanged.connect(lambda: updateFiducialComboBox())
    #     self.payloadWidget.model.dataChanged.connect(lambda: updateFiducialComboBox())


class DeviceListView(QWidget):
    def __init__(self, *args, devices: List[Device] = None, **kwargs):
        super().__init__(*args, **kwargs)

        self._devices = devices or []

        self.setUpUI()
        self.setUpReactivity()

    def setUpUI(self):
        deviceTabWidget = QTabWidget()
        self.tabWidget = deviceTabWidget

        addDeviceButton = QPushButton()
        addDeviceButton.setText("Add device")
        self.addDeviceButton = addDeviceButton

        deleteDeviceButton = QPushButton()
        deleteDeviceButton.setObjectName("DeleteDeviceButton")
        deleteDeviceButton.setText("Delete device")
        deleteDeviceButton.setEnabled(self.tabWidget.count() >= 2)
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
            index = self.tabWidget.indexOf(widget)
            widget.nameLabelEdit.textChanged.connect(
                lambda name: self.tabWidget.setTabText(index, name)
            )
            self.tabWidget.setCurrentIndex(index)

            self._updateDeleteButton()

        self.addDeviceButton.clicked.connect(lambda: addNewDevice())

        def deleteDevice():
            index = self.tabWidget.currentIndex()
            name = self.tabWidget.tabText(index)

            msgBox = QMessageBox()
            msgBox.setWindowTitle(f"Delete {name}?")
            msgBox.setIcon(QMessageBox.Question)
            msgBox.setText(f"Are you sure you want to delete {name}?")
            msgBox.setWindowModality(Qt.ApplicationModal)
            msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msgBox.setDefaultButton(QMessageBox.No)

            response = msgBox.exec_()
            if response == QMessageBox.Yes:
                self.tabWidget.removeTab(index)

                self._updateDeleteButton()

        self.deleteDeviceButton.clicked.connect(lambda: deleteDevice())


class DeviceEditor:
    def __init__(self, devices: List[Device] = None):
        self.devices = devices or []


if __name__ == "__main__":
    import sys
    from PySide2.QtWidgets import QApplication

    app = QApplication()
    widget = DeviceListView()
    widget.show()
    sys.exit(app.exec_())
