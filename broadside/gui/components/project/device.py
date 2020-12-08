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

from .payload import FormulationTableEditorView
from ..editor import Editor
from ..utils import showYesNoDialog
from ...color import Color
from ...models.device import (
    Device,
    LongitudinalDirection,
    LongitudinalOrientation,
    AngularDirection,
)


class DeviceEditorView(QWidget):
    dataChanged = Signal()

    def __init__(self, device: Device, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.device = device

        self.setUpUI()
        self.setUpReactivity()

    def setUpUI(self):
        nameLabel = QLabel("Name:")
        nameLineEdit = QLineEdit()
        nameLineEdit.setMinimumWidth(150)
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

        formulationTableEditorView = FormulationTableEditorView(self.device.payload)
        formulationTableEditorView.setMaximumWidth(600)
        self.formulationTableEditorView = formulationTableEditorView

        layout = QGridLayout()
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 1)

        layout.addWidget(nameLabel, 0, 0, Qt.AlignRight)
        layout.addWidget(nameLineEdit, 0, 1, Qt.AlignLeft)
        layout.setRowStretch(0, 0)

        layout.addWidget(longOrientLabel, 1, 0, Qt.AlignRight)
        layout.addWidget(longOrientCombo, 1, 1, Qt.AlignLeft)
        layout.setRowStretch(1, 0)

        layout.addWidget(longDirLabel, 2, 0, Qt.AlignRight)
        layout.addWidget(longDirCombo, 2, 1, Qt.AlignLeft)
        layout.setRowStretch(2, 0)

        layout.addWidget(angDirLabel, 3, 0, Qt.AlignRight)
        layout.addWidget(angDirCombo, 3, 1, Qt.AlignLeft)
        layout.setRowStretch(3, 0)

        layout.addWidget(formulationTableEditorView, 4, 0, 1, 2)
        layout.setRowStretch(4, 0)

        layout.addWidget(QWidget(), 5, 0)
        layout.setRowStretch(5, 1)

        self.setLayout(layout)

    def setUpReactivity(self):
        def onNameChange():
            name = self.nameLineEdit.text()
            self.device.name = name
            self.dataChanged.emit()

        self.nameLineEdit.textChanged.connect(lambda: onNameChange())

        def onLongitudinalOrientationChange():
            longOrient = LongitudinalOrientation(
                self.longitudinalOrientationComboBox.currentText()
            )
            self.device.longitudinalOrientation = longOrient
            self.dataChanged.emit()

        self.longitudinalOrientationComboBox.currentIndexChanged.connect(
            lambda: onLongitudinalOrientationChange()
        )

        def onLongitudinalDirectionChange():
            longDir = LongitudinalDirection(
                self.longitudinalDirectionComboBox.currentText()
            )
            self.device.longitudinalDirection = longDir
            self.dataChanged.emit()

        self.longitudinalDirectionComboBox.currentIndexChanged.connect(
            lambda: onLongitudinalDirectionChange()
        )

        # populate fields
        self.nameLineEdit.setText(self.device.name)
        longOrient = self.device.longitudinalOrientation
        if longOrient is None:
            self.longitudinalOrientationComboBox.setCurrentIndex(0)
            self.device.longitudinalOrientation = LongitudinalOrientation(
                self.longitudinalOrientationComboBox.itemText(0)
            )
        else:
            self.longitudinalOrientationComboBox.setCurrentText(longOrient.value)

        longDir = self.device.longitudinalDirection
        if longDir is None:
            self.longitudinalDirectionComboBox.setCurrentIndex(0)
            self.device.longitudinalDirection = LongitudinalDirection(
                self.longitudinalDirectionComboBox.itemText(0)
            )
        else:
            self.longitudinalDirectionComboBox.setCurrentText(longDir.value)

        angDir = self.device.angularDirection
        if angDir is None:
            self.angularDirectionComboBox.setCurrentIndex(0)
            self.device.angularDirection = AngularDirection(
                self.angularDirectionComboBox.itemText(0)
            )
        else:
            self.angularDirectionComboBox.setCurrentText(angDir.value)

        self.formulationTableEditorView.dataChanged.connect(
            lambda: self.dataChanged.emit()
        )


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

    def updateDeleteDeviceButton(self) -> None:
        self.deleteDeviceButton.setEnabled(self.tabWidget.count() >= 2)

    def addDevice(self, device: Device) -> None:
        deviceEditor = DeviceEditorView(device)
        deviceEditor.dataChanged.connect(lambda: self.dataChanged.emit())
        self.tabWidget.addTab(deviceEditor, device.name)

        index = self.tabWidget.indexOf(deviceEditor)
        deviceEditor.nameLineEdit.textChanged.connect(
            lambda: self.tabWidget.setTabText(index, deviceEditor.nameLineEdit.text())
        )
        self.tabWidget.setCurrentIndex(index)

        self.updateDeleteDeviceButton()

    def deleteDevice(self, index: int) -> None:
        self.tabWidget.removeTab(index)

        self.updateDeleteDeviceButton()


class DeviceListEditor(Editor):
    log = logging.getLogger(__name__)

    def __init__(self, devices: List[Device], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.devices = devices

        # set up view reactivity
        self.view = DeviceListEditorView()
        self.view.addDeviceButton.clicked.connect(lambda: self.addDevice())
        self.view.deleteDeviceButton.clicked.connect(lambda: self.deleteCurrentDevice())
        self.view.dataChanged.connect(lambda: self.dataChanged.emit())

        # initialize view
        for device in self.devices:
            self.view.addDevice(device)
        self.view.tabWidget.setCurrentIndex(0)

        tabBar: QTabBar = self.view.tabWidget.tabBar()
        tabBar.tabMoved.connect(lambda to_, from_: self.moveDevice(to_, from_))
        self.tabBar = tabBar

        # set up remaining reactivity
        self.dataChanged.connect(lambda: self.validate())

        # initialize
        self.validate()

    def addDevice(self) -> None:
        count = self.view.tabWidget.count() + 1
        device = Device.from_dict({"name": f"New device {count}"})
        self.devices.append(device)
        self.view.addDevice(device)

        self.dataChanged.emit()
        self.log.info("New device added")

    def deleteCurrentDevice(self) -> None:
        index = self.view.tabWidget.currentIndex()
        name = self.view.tabWidget.tabText(index) or "the current device"

        response = showYesNoDialog(
            parent=self.view,
            title=f"Delete {name}?",
            text=f"Are you sure you want to delete {name}?",
        )
        if response == QMessageBox.Yes:
            del self.devices[index]
            self.view.deleteDevice(index)

            self.dataChanged.emit()
            self.log.info("Device deleted")

    def moveDevice(self, to_: int, from_: int) -> None:
        (self.devices[to_], self.devices[from_]) = (
            self.devices[from_],
            self.devices[to_],
        )

        self.dataChanged.emit()
        self.log.info(f"Device moved to {to_} from {from_}")

    def validate(self):
        names = [d.name for d in self.devices]
        namesAsSet = set(names)

        self.isValid = len(namesAsSet) == len(names)

        duplicates = set()
        for name in namesAsSet:
            indexes = [i for i, _name in enumerate(names) if _name == name]
            if len(indexes) > 1:
                duplicates.update(indexes)

        for index in range(self.tabBar.count()):
            if index in duplicates:
                self.tabBar.setTabTextColor(index, Color.Red.qc())
            else:
                self.tabBar.setTabTextColor(index, Color.Black.qc())
