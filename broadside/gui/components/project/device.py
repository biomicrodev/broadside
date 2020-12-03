import logging
from typing import List

from PySide2.QtCore import Signal, Qt, QObject
from PySide2.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QPushButton,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QGridLayout,
    QComboBox,
    QTabBar,
    QMessageBox,
)

from ..utils import showYesNoDialog
from ...models.device import (
    Device,
    LongitudinalDirection,
    LongitudinalOrientation,
    AngularDirection,
)


class DeviceEditor(QWidget):
    dataChanged = Signal()

    def __init__(self, device: Device, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setUpUI()

        # set up reactivity
        def onNameChange():
            name = self.nameLineEdit.text()
            device.name = name
            self.dataChanged.emit()

        self.nameLineEdit.textChanged.connect(lambda: onNameChange())

        def onLongitudinalOrientationChange():
            longOrient = LongitudinalOrientation(
                self.longitudinalOrientationComboBox.currentText()
            )
            device.longitudinalOrientation = longOrient
            self.dataChanged.emit()

        self.longitudinalOrientationComboBox.currentIndexChanged.connect(
            lambda: onLongitudinalOrientationChange()
        )

        def onLongitudinalDirectionChange():
            longDir = LongitudinalDirection(
                self.longitudinalDirectionComboBox.currentText()
            )
            device.longitudinalDirection = longDir
            self.dataChanged.emit()

        self.longitudinalDirectionComboBox.currentIndexChanged.connect(
            lambda: onLongitudinalDirectionChange()
        )

        # populate fields
        self.nameLineEdit.setText(device.name)
        longOrient = device.longitudinalOrientation
        if longOrient is None:
            self.longitudinalOrientationComboBox.setCurrentIndex(0)
            device.longitudinalOrientation = LongitudinalOrientation(
                self.longitudinalOrientationComboBox.itemText(0)
            )
        else:
            self.longitudinalOrientationComboBox.setCurrentText(longOrient.value)

        longDir = device.longitudinalDirection
        if longDir is None:
            self.longitudinalDirectionComboBox.setCurrentIndex(0)
            device.longitudinalDirection = LongitudinalDirection(
                self.longitudinalDirectionComboBox.itemText(0)
            )
        else:
            self.longitudinalDirectionComboBox.setCurrentText(longDir.value)

        angDir = device.angularDirection
        if angDir is None:
            self.angularDirectionComboBox.setCurrentIndex(0)
            device.angularDirection = AngularDirection(
                self.angularDirectionComboBox.itemText(0)
            )
        else:
            self.angularDirectionComboBox.setCurrentText(angDir.value)

    def setUpUI(self):
        nameLabel = QLabel("Name:")
        nameLineEdit = QLineEdit()
        nameLabel.setBuddy(nameLineEdit)
        self.nameLineEdit = nameLineEdit

        longOrientLabel = QLabel("Longitudinal orientation:")
        longOrientCombo = QComboBox()
        longOrientCombo.addItems(
            [
                LongitudinalOrientation.TipIntoPage.value,
                LongitudinalOrientation.TipOutOfPage.value,
            ]
        )
        longOrientLabel.setBuddy(longOrientCombo)
        self.longitudinalOrientationComboBox = longOrientCombo

        longDirLabel = QLabel("Longitudinal direction:")
        longDirCombo = QComboBox()
        longDirCombo.addItems(
            [
                LongitudinalDirection.IncreasingTowardsTip.value,
                LongitudinalDirection.IncreasingTowardsBooster.value,
            ]
        )
        longDirLabel.setBuddy(longDirCombo)
        self.longitudinalDirectionComboBox = longDirCombo

        angDirLabel = QLabel("Angular direction:")
        angDirCombo = QComboBox()
        angDirCombo.addItems(
            [AngularDirection.Clockwise.value, AngularDirection.CounterClockwise.value]
        )
        angDirLabel.setBuddy(angDirCombo)
        self.angularDirectionComboBox = angDirCombo

        layout = QGridLayout()
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 1)

        layout.addWidget(nameLabel, 0, 0, Qt.AlignRight)
        layout.addWidget(nameLineEdit, 0, 1, Qt.AlignLeft)
        layout.setRowStretch(0, 0)

        layout.addWidget(longDirLabel, 1, 0, Qt.AlignRight)
        layout.addWidget(longDirCombo, 1, 1, Qt.AlignLeft)
        layout.setRowStretch(1, 0)

        layout.addWidget(angDirLabel, 2, 0, Qt.AlignRight)
        layout.addWidget(angDirCombo, 2, 1, Qt.AlignLeft)

        layout.addWidget(QWidget(), 3, 0)
        layout.setRowStretch(3, 1)

        self.setLayout(layout)


class DeviceListEditorView(QWidget):
    dataChanged = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setUpUI()

        self.updateDeleteDeviceButton()

    def setUpUI(self):
        tabWidget = QTabWidget()
        tabWidget.setMovable(True)
        self.tabWidget = tabWidget

        addDeviceButton = QPushButton()
        addDeviceButton.setText("Add device")
        self.addDeviceButton = addDeviceButton

        deleteDeviceButton = QPushButton()
        deleteDeviceButton.setText("Delete device")
        deleteDeviceButton.setObjectName("deleteDeviceButton")
        self.deleteDeviceButton = deleteDeviceButton

        buttonsLayout = QHBoxLayout()
        buttonsLayout.addWidget(addDeviceButton)
        buttonsLayout.addWidget(deleteDeviceButton)

        layout = QVBoxLayout()
        layout.addWidget(tabWidget)
        layout.addLayout(buttonsLayout)
        self.setLayout(layout)

    def updateDeleteDeviceButton(self):
        self.deleteDeviceButton.setEnabled(self.tabWidget.count() >= 2)

    def addDevice(self, device: Device):
        deviceEditor = DeviceEditor(device)
        deviceEditor.dataChanged.connect(lambda: self.dataChanged.emit())
        self.tabWidget.addTab(deviceEditor, device.name)

        index = self.tabWidget.indexOf(deviceEditor)
        deviceEditor.nameLineEdit.textChanged.connect(
            lambda: self.tabWidget.setTabText(index, deviceEditor.nameLineEdit.text())
        )
        self.tabWidget.setCurrentIndex(index)

        self.updateDeleteDeviceButton()

    def deleteCurrentDevice(self):
        index = self.tabWidget.currentIndex()
        self.tabWidget.removeTab(index)

        self.updateDeleteDeviceButton()


class DeviceListEditor(QObject):
    log = logging.getLogger(__name__)

    dataChanged = Signal()

    def __init__(self, devices: List[Device], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.devices = devices

        self.view = DeviceListEditorView()
        for device in self.devices:
            self.view.addDevice(device)

        self.view.addDeviceButton.clicked.connect(lambda: self.addDevice())
        self.view.deleteDeviceButton.clicked.connect(lambda: self.deleteCurrentDevice())
        self.view.dataChanged.connect(lambda: self.dataChanged.emit())

        tabBar: QTabBar = self.view.tabWidget.tabBar()
        tabBar.tabMoved.connect(lambda to_, from_: self.moveDevice(to_, from_))
        self.tabBar = tabBar

    def addDevice(self):
        count = self.view.tabWidget.count() + 1
        device = Device(name=f"New device {count}")
        self.devices.append(device)
        self.view.addDevice(device)

        self.dataChanged.emit()
        self.log.info("New device added")

    def deleteCurrentDevice(self):
        index = self.view.tabWidget.currentIndex()
        name = self.view.tabWidget.tabText(index) or "the current device"

        response = showYesNoDialog(
            parent=self.view,
            title=f"Delete {name}?",
            text=f"Are you sure you want to delete {name}?",
        )
        if response == QMessageBox.Yes:
            del self.devices[index]
            self.view.deleteCurrentDevice()

            self.dataChanged.emit()
            self.log.info("Device deleted")

    def moveDevice(self, to_: int, from_: int):
        (self.devices[to_], self.devices[from_]) = (
            self.devices[from_],
            self.devices[to_],
        )

        self.dataChanged.emit()
        self.log.info(f"Device moved to {to_} from {from_}")
