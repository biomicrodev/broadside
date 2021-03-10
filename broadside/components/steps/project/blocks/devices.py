import copy
import logging
from typing import Any, List, Tuple

from natsort import natsort_keygen
from qtpy.QtCore import QAbstractTableModel, Qt, QModelIndex, QItemSelectionModel
from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableView,
    QAbstractItemView,
    QHeaderView,
    QPushButton,
    QHBoxLayout,
    QGroupBox,
)

from ....utils import CellState, LineEditItemDelegate, NamesDelegate
from .....models.block import Device, Sample
from .....models.payload import Payload
from .....utils.events import EventedList


class DevicesTableModel(QAbstractTableModel):
    def __init__(self, devices: EventedList[Device], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.devices = devices

    def data(self, index: QModelIndex, role: Qt.ItemDataRole = None) -> Any:
        if role in [Qt.DisplayRole, Qt.EditRole, Qt.ToolTipRole]:
            key = Device.keys[index.column()]
            value = getattr(self.devices[index.row()], key)
            return value

        elif role == Qt.BackgroundRole:
            row = index.row()
            key = Device.keys[index.column()]
            value = getattr(self.devices[row], key)

            if value == "":
                return CellState.Invalid

            if key == "name":
                name = value
                otherDeviceNames = [
                    d.name for i, d in enumerate(self.devices) if i != row
                ]
                if name in otherDeviceNames:
                    return CellState.Invalid

            # otherwise ...
            return CellState.Valid

        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter

    def setData(
        self, index: QModelIndex, value: Any, role: Qt.ItemDataRole = None
    ) -> bool:
        if role == Qt.EditRole:
            row = index.row()
            col = index.column()

            key = Device.keys[col]
            type_ = Device.types[col]

            try:
                value = type_(value)
            except ValueError:
                return False

            setattr(self.devices[row], key, value)
            self.dataChanged.emit(index, index, [Qt.EditRole])
            return True

        return False

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        return super().flags(index) | Qt.ItemIsEditable

    def rowCount(self, parent: QModelIndex = None, *args, **kwargs) -> int:
        return len(self.devices)

    def columnCount(self, parent: QModelIndex = None, *args, **kwargs) -> int:
        return len(Device.keys)

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole = None
    ) -> Any:
        if role == Qt.DisplayRole:
            # column headers
            if orientation == Qt.Horizontal:
                return Device.headers[section]

            # row headers
            elif orientation == Qt.Vertical:
                return section + 1  # section is 0-indexed


class DevicesTableView(QTableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setSelectionMode(QAbstractItemView.SingleSelection)
        horizontalHeader: QHeaderView = self.horizontalHeader()
        horizontalHeader.setStretchLastSection(True)

        delegate = LineEditItemDelegate(parent=self)
        self.setItemDelegate(delegate)


class DevicesEditorView(QWidget):
    def __init__(self, tableView: DevicesTableView):
        super().__init__()

        self.tableView = tableView

        self.initUI()
        self.initBindings()

    def initUI(self):
        addDeviceButton = QPushButton()
        addDeviceButton.setText("Add device")
        addDeviceButton.setCursor(Qt.PointingHandCursor)
        self.addDeviceButton = addDeviceButton

        deleteDeviceButton = QPushButton()
        deleteDeviceButton.setText("Delete device")
        deleteDeviceButton.setObjectName("deleteDeviceButton")
        deleteDeviceButton.setDisabled(True)
        deleteDeviceButton.setCursor(Qt.ForbiddenCursor)
        self.deleteDeviceButton = deleteDeviceButton

        sortDevicesButton = QPushButton()
        sortDevicesButton.setText("Sort")
        sortDevicesButton.setCursor(Qt.PointingHandCursor)
        self.sortDevicesButton = sortDevicesButton

        buttonsLayout = QHBoxLayout()
        buttonsLayout.addWidget(addDeviceButton)
        buttonsLayout.addWidget(deleteDeviceButton)
        buttonsLayout.addWidget(sortDevicesButton)

        layout = QVBoxLayout()
        layout.addWidget(self.tableView, 1)
        layout.addLayout(buttonsLayout, 0)

        groupBox = QGroupBox()
        groupBox.setTitle("Devices")
        groupBox.setLayout(layout)

        parentLayout = QVBoxLayout()
        parentLayout.addWidget(groupBox)
        self.setLayout(parentLayout)

    def initBindings(self):
        selectionModel: QItemSelectionModel = self.tableView.selectionModel()
        selectionModel.selectionChanged.connect(lambda: self.updateButtons())

    def updateButtons(self):
        indexes: List[int] = self.tableView.selectedIndexes()
        self.deleteDeviceButton.setEnabled(len(indexes) > 0)
        self.deleteDeviceButton.setCursor(
            Qt.PointingHandCursor if (len(indexes) > 0) else Qt.ForbiddenCursor
        )


def device_key(d: Device) -> Tuple[bool, str]:
    return (d.name == ""), d.name


class DevicesEditor:
    log = logging.getLogger(__name__)

    def __init__(
        self,
        devices: EventedList[Device],
        payloads: EventedList[Payload],
        samples: EventedList[Sample],
    ):
        self.devices = devices
        self.payloads = payloads
        self.samples = samples

        # set up Qt model/view for payload and sample names
        payload_names_delegate = NamesDelegate(payloads)
        sample_names_delegate = NamesDelegate(samples)

        # set up Qt model/view for devices
        self._model = DevicesTableModel(devices)

        table_view = DevicesTableView()
        table_view.setModel(self._model)
        table_view.setItemDelegateForColumn(1, payload_names_delegate._view)
        table_view.setItemDelegateForColumn(2, sample_names_delegate._view)
        self._view = DevicesEditorView(table_view)

        # bindings from view to model
        self._view.addDeviceButton.clicked.connect(lambda _: self.add_device())
        self._view.deleteDeviceButton.clicked.connect(lambda _: self.delete_device())
        self._view.sortDevicesButton.clicked.connect(lambda _: self.sort_devices())

        # bindings from model to view
        self.devices.events.changed.connect(lambda _: self._view.updateButtons())

        payloads.events.deleted.connect(lambda _: self._validate_payload_names())
        payloads.events.added.connect(lambda d: self._add_payload_bindings(d["item"]))
        for payload in payloads:
            self._add_payload_bindings(payload)

        samples.events.deleted.connect(lambda _: self._validate_sample_names())
        samples.events.added.connect(lambda d: self._add_sample_bindings(d["item"]))
        for sample in samples:
            self._add_sample_bindings(sample)

    def _validate_payload_names(self):
        payload_names = [payload.name for payload in self.payloads]
        for device in self.devices:
            if device.payload_name not in payload_names:
                device.payload_name = ""

    def _validate_sample_names(self):
        sample_names = [sample.name for sample in self.samples]
        for device in self.devices:
            if device.sample_name not in sample_names:
                device.sample_name = ""

    def _add_payload_bindings(self, payload: Payload):
        def update(old_name: str, new_name: str):
            indexes_to_update = []
            for i, device in enumerate(self.devices):
                if device.payload_name == old_name:
                    device.payload_name = new_name
                    indexes_to_update.append(i)

            col = Device.keys.index("payload_name")
            for i in indexes_to_update:
                index = self._model.index(i, col)
                self._model.dataChanged.emit(index, index, [Qt.EditRole])

        payload.events.name.connect(lambda d: update(d["old"], d["new"]))

    def _add_sample_bindings(self, sample: Sample):
        def update(old_name: str, new_name: str):
            indexes_to_update = []

            for i, device in enumerate(self.devices):
                if device.sample_name == old_name:
                    device.sample_name = new_name
                    indexes_to_update.append(i)

            col = Device.keys.index("sample_name")
            for i in indexes_to_update:
                index = self._model.index(i, col)
                self._model.dataChanged.emit(index, index, [Qt.EditRole])

        sample.events.name.connect(lambda d: update(d["old"], d["new"]))

    def add_device(self):
        # update model
        row = len(self.devices)

        index = self._model.index(row, 0)
        self._model.layoutAboutToBeChanged.emit()
        self._model.beginInsertRows(index, row, row)

        self.devices.append(Device(name=f"Device {row + 1}"))

        self._model.endInsertRows()
        self._model.layoutChanged.emit()

        # update view
        self._view.tableView.setCurrentIndex(index)
        self._view.tableView.setFocus()

    def delete_device(self):
        indexes: List[QModelIndex] = self._view.tableView.selectedIndexes()
        index = indexes[0]
        row = index.row()

        # update model
        self._model.layoutAboutToBeChanged.emit()
        self._model.beginRemoveRows(index, row, row)

        del self.devices[row]

        self._model.endRemoveRows()
        self._model.layoutChanged.emit()

        # update view
        if row >= len(self.devices):
            self._view.tableView.clearSelection()
        else:
            self._view.tableView.setCurrentIndex(index)
            self._view.tableView.setFocus()

    def sort_devices(self):
        natkey = natsort_keygen(key=device_key)

        old_devices = copy.copy(self.devices)
        self.devices.sort(key=natkey)
        if self.devices != old_devices:
            self._model.layoutChanged.emit()
