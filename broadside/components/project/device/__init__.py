import logging
from typing import Set, List

from PySide2.QtCore import Signal, Qt
from PySide2.QtWidgets import (
    QWidget,
    QLabel,
    QComboBox,
    QGridLayout,
    QScrollArea,
    QVBoxLayout,
    QTabBar,
    QMessageBox,
)

from .payload import FormulationTableEditorView
from ...color import Color
from ...editor import Editor
from ...utils import EditableTabWidget, showYesNoDialog
from ...viewermodel import ViewerModel
from ....models.device import (
    Device,
    LongitudinalOrientation,
    LongitudinalDirection,
    AngularDirection,
)


class DeviceEditorView(QWidget):
    deviceChanged = Signal()

    def __init__(self, device: Device, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.device = device

        self.initUI()
        self.initBindings()

    def initUI(self):
        longOrientLabel = QLabel("Longitudinal orientation:")
        longOrientCombo = QComboBox()
        longOrientCombo.addItems(
            [
                LongitudinalOrientation.TipIntoPage.value,
                LongitudinalOrientation.TipOutOfPage.value,
            ]
        )
        longOrientLabel.setBuddy(longOrientCombo)
        self.longOrientCombo = longOrientCombo

        longDirLabel = QLabel("Longitudinal direction:")
        longDirCombo = QComboBox()
        longDirCombo.addItems(
            [
                LongitudinalDirection.IncreasingTowardsTip.value,
                LongitudinalDirection.IncreasingTowardsBooster.value,
            ]
        )
        longDirLabel.setBuddy(longDirCombo)
        self.longDirCombo = longDirCombo

        angDirLabel = QLabel("Angular direction:")
        angDirCombo = QComboBox()
        angDirCombo.addItems(
            [AngularDirection.Clockwise.value, AngularDirection.CounterClockwise.value]
        )
        angDirLabel.setBuddy(angDirCombo)
        self.angDirCombo = angDirCombo

        formulationTableEditorView = FormulationTableEditorView(self.device.payload)
        formulationTableEditorView.setMinimumHeight(500)
        formulationTableEditorView.setMaximumWidth(600)
        self.formulationTableEditorView = formulationTableEditorView

        layout = QGridLayout()
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 1)

        layout.addWidget(longOrientLabel, 0, 0, Qt.AlignRight)
        layout.addWidget(longOrientCombo, 0, 1, Qt.AlignLeft)
        layout.setRowStretch(0, 0)

        layout.addWidget(longDirLabel, 1, 0, Qt.AlignRight)
        layout.addWidget(longDirCombo, 1, 1, Qt.AlignLeft)
        layout.setRowStretch(1, 0)

        layout.addWidget(angDirLabel, 2, 0, Qt.AlignRight)
        layout.addWidget(angDirCombo, 2, 1, Qt.AlignLeft)
        layout.setRowStretch(2, 0)

        layout.addWidget(formulationTableEditorView, 3, 0, 1, 2)
        layout.setRowStretch(3, 1)

        layout.addWidget(QWidget(), 4, 0)
        layout.setRowStretch(4, 1)

        parentWidget = QWidget()
        parentWidget.setLayout(layout)
        parentWidget.setMinimumWidth(600)

        scrollArea = QScrollArea()
        scrollArea.setWidget(parentWidget)
        scrollArea.setWidgetResizable(True)

        parentLayout = QVBoxLayout()
        parentLayout.addWidget(scrollArea, 1)
        self.setLayout(parentLayout)

    def initBindings(self):
        def onLongOrientChange():
            longOrient = LongitudinalOrientation(self.longOrientCombo.currentText())
            self.device.longitudinal_orientation = longOrient
            self.deviceChanged.emit()

        self.longOrientCombo.currentIndexChanged.connect(lambda: onLongOrientChange())

        def onLongDirChange():
            longDir = LongitudinalDirection(self.longDirCombo.currentText())
            self.device.longitudinal_direction = longDir
            self.deviceChanged.emit()

        self.longDirCombo.currentIndexChanged.connect(lambda: onLongDirChange())

        def onAngDirChange():
            angDir = AngularDirection(self.angDirCombo.currentText())
            self.device.angular_direction = angDir
            self.deviceChanged.emit()

        self.angDirCombo.currentIndexChanged.connect(lambda: onAngDirChange())

        self.formulationTableEditorView.formulationListChanged.connect(
            lambda: self.deviceChanged.emit()
        )

        # populate fields
        longOrient = self.device.longitudinal_orientation
        if longOrient is None:
            self.longOrientCombo.setCurrentIndex(0)
            self.device.longitudinal_orientation = LongitudinalOrientation(
                self.longOrientCombo.currentText()
            )
        else:
            self.longOrientCombo.setCurrentText(longOrient.value)

        longDir = self.device.longitudinal_direction
        if longDir is None:
            self.longDirCombo.setCurrentIndex(0)
            self.device.longitudinal_direction = LongitudinalDirection(
                self.longDirCombo.currentText()
            )
        else:
            self.longDirCombo.setCurrentText(longDir.value)

        angDir = self.device.angular_direction
        if angDir is None:
            self.angDirCombo.setCurrentIndex(0)
            self.device.angular_direction = AngularDirection(
                self.angDirCombo.currentText()
            )
        else:
            self.angDirCombo.setCurrentText(angDir.value)


class DeviceListEditorView(QWidget):
    deviceListChanged = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.tabWidget = EditableTabWidget(addButtonText="Add new device")

        layout = QVBoxLayout()
        layout.addWidget(self.tabWidget)
        self.setLayout(layout)

    def addDevice(self, device: Device) -> None:
        deviceEditor = DeviceEditorView(device)
        deviceEditor.deviceChanged.connect(lambda: self.deviceListChanged.emit())
        self.tabWidget.addTab(deviceEditor, device.name)
        self.tabWidget.setCurrentWidget(deviceEditor)

    def deleteDevice(self, index: int) -> None:
        self.tabWidget.removeTab(index)

    def styleInvalidTabs(self, indexes: Set[int]) -> None:
        tabBar: QTabBar = self.tabWidget.tabBar()
        for index in range(tabBar.count()):
            tabBar.setTabTextColor(
                index, Color.Red.qc() if index in indexes else Color.Black.qc()
            )

    def refresh(self):
        pass


class DeviceListEditor(Editor):
    log = logging.getLogger(__name__)

    deviceListChanged = Signal()

    def __init__(self, model: ViewerModel, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.model = model
        self.devices = model.state.devices  # for convenience, mostly
        self.view = DeviceListEditorView()

        # set up bindings
        self.view.deviceListChanged.connect(lambda: self.deviceListChanged.emit())
        self.deviceListChanged.connect(lambda: self.validate())

        tabWidget = self.view.tabWidget
        tabWidget.addTabButton.clicked.connect(lambda: self.addDevice())
        tabWidget.tabCloseRequested.connect(lambda index: self.deleteDevice(index))
        tabWidget.tabMoved.connect(lambda to_, from_: self.moveDevice(to_, from_))

        def updateName(index: int) -> None:
            name = tabWidget.tabText(index)
            if self.devices[index].name != name:
                self.devices[index].name = name
                self.deviceListChanged.emit()

        tabWidget.editingFinished.connect(lambda index: updateName(index))

        # initialize
        for device in self.devices:
            self.view.addDevice(device)
        self.view.tabWidget.setCurrentIndex(0)

        self.validate()

    def addDevice(self) -> None:
        count = self.view.tabWidget.count() + 1
        device = Device.from_dict({"name": f"New device {count}"})
        self.devices.append(device)
        self.view.addDevice(device)

        self.deviceListChanged.emit()
        self.log.info("New device added")

    def deleteDevice(self, index: int) -> None:
        name = self.view.tabWidget.tabText(index) or "the current device"

        response = showYesNoDialog(
            parent=self.view,
            title=f"Delete {name}?",
            text=f"Are you sure you want to delete {name}?",
        )
        if response == QMessageBox.Yes:
            del self.devices[index]
            self.view.deleteDevice(index)

            self.deviceListChanged.emit()
            self.log.info("Device deleted")

    def moveDevice(self, to_: int, from_: int) -> None:
        (self.devices[to_], self.devices[from_]) = (
            self.devices[from_],
            self.devices[to_],
        )

        self.deviceListChanged.emit()
        self.log.info(f"Device moved to {to_} from {from_}")

    def validate(self) -> None:
        invalidDeviceIndexes = self.model.state.invalid_device_indexes()
        self.view.styleInvalidTabs(invalidDeviceIndexes)
        self.isValid = len(invalidDeviceIndexes) == 0
