import logging
from typing import Set

from qtpy.QtCore import Qt
from qtpy.QtGui import QColor
from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabBar,
    QLabel,
    QComboBox,
    QGridLayout,
    QScrollArea,
    QMessageBox,
    QLineEdit,
    QPlainTextEdit,
    QGroupBox,
    QHBoxLayout,
)

from .formulations import FormulationsEditor, FormulationsEditorView
from ....editor import Editor
from ....utils import EditableTabWidget, showYesNoDialog
from ....viewer_model import ViewerModel
from .....models.payload import Payload, LongOrient, LongDir, AngDir, Formulation
from .....utils.colors import Color


class PayloadEditorView(QWidget):
    def __init__(self, formulationsEditorView: FormulationsEditorView, *args, **kwargs):
        super().__init__(*args, **kwargs)

        longOrientLabel = QLabel("Longitudinal orientation:")
        longOrientCombo = QComboBox()
        longOrientCombo.addItems(
            [
                LongOrient.TipIntoPage.value,
                LongOrient.TipOutOfPage.value,
            ]
        )
        longOrientLabel.setBuddy(longOrientCombo)
        self.longOrientCombo = longOrientCombo

        longDirLabel = QLabel("Longitudinal direction:")
        longDirCombo = QComboBox()
        longDirCombo.addItems(
            [
                LongDir.IncreasingTowardsTip.value,
                LongDir.IncreasingTowardsBooster.value,
            ]
        )
        longDirLabel.setBuddy(longDirCombo)
        self.longDirCombo = longDirCombo

        angDirLabel = QLabel("Angular direction:")
        angDirCombo = QComboBox()
        angDirCombo.addItems([AngDir.Clockwise.value, AngDir.CounterClockwise.value])
        angDirLabel.setBuddy(angDirCombo)
        self.angDirCombo = angDirCombo

        notesTextEdit = QPlainTextEdit()
        self.notesTextEdit = notesTextEdit
        notesLayout = QHBoxLayout()
        notesLayout.addWidget(notesTextEdit)
        notesGroupBox = QGroupBox()
        notesGroupBox.setTitle("Notes")
        notesGroupBox.setLayout(notesLayout)
        notesGroupBox.setMaximumWidth(400)
        notesGroupBox.setMaximumHeight(200)

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

        layout.addWidget(formulationsEditorView, 3, 0, 1, 2)
        layout.setRowStretch(3, 1)

        layout.addWidget(notesGroupBox, 4, 0, 1, 2)
        layout.setRowStretch(4, 0)

        layout.addWidget(QWidget(), 5, 0)
        layout.setRowStretch(5, 0)

        parentWidget = QWidget()
        parentWidget.setLayout(layout)

        scrollArea = QScrollArea()
        scrollArea.setWidget(parentWidget)
        scrollArea.setWidgetResizable(True)

        parentLayout = QVBoxLayout()
        parentLayout.addWidget(scrollArea, 1)
        self.setLayout(parentLayout)


class PayloadEditor:
    def __init__(
        self, payload: Payload, formulations_editor_view: FormulationsEditorView
    ):
        self._view = PayloadEditorView(formulationsEditorView=formulations_editor_view)

        # init bindings
        def set_long_orient():
            payload.long_orient = LongOrient(self._view.longOrientCombo.currentText())

        self._view.longOrientCombo.currentIndexChanged.connect(
            lambda: set_long_orient()
        )

        def set_long_dir():
            payload.long_dir = LongDir(self._view.longDirCombo.currentText())

        self._view.longDirCombo.currentIndexChanged.connect(lambda: set_long_dir())

        def set_ang_dir():
            payload.ang_dir = AngDir(self._view.angDirCombo.currentText())

        self._view.angDirCombo.currentIndexChanged.connect(lambda: set_ang_dir())

        def set_notes():
            payload.notes = self._view.notesTextEdit.toPlainText()

        self._view.notesTextEdit.textChanged.connect(lambda: set_notes())

        # populate fields
        if payload.long_orient is None:
            self._view.longOrientCombo.setCurrentIndex(0)
            payload.long_orient = LongOrient(self._view.longOrientCombo.currentText())
        else:
            self._view.longOrientCombo.setCurrentText(payload.long_orient.value)

        if payload.long_dir is None:
            self._view.longDirCombo.setCurrentIndex(0)
            payload.long_dir = LongDir(self._view.longDirCombo.currentText())
        else:
            self._view.longDirCombo.setCurrentText(payload.long_dir.value)

        if payload.ang_dir is None:
            self._view.angDirCombo.setCurrentIndex(0)
            payload.ang_dir = AngDir(self._view.angDirCombo.currentText())
        else:
            self._view.angDirCombo.setCurrentText(payload.ang_dir.value)

        self._view.notesTextEdit.setPlainText(payload.notes)


class PayloadsEditorView(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.tabWidget = EditableTabWidget(addButtonText="Add new payload")

        layout = QVBoxLayout()
        layout.addWidget(self.tabWidget)
        self.setLayout(layout)

    def styleInvalidTabs(self, indexes: Set[int]) -> None:
        tabBar: QTabBar = self.tabWidget.tabBar()
        for index in range(tabBar.count()):
            tabBar.setTabTextColor(
                index, QColor(*(Color.Red if index in indexes else Color.Black).value)
            )


class PayloadsEditor(Editor):
    log = logging.getLogger(__name__)

    def __init__(self, model: ViewerModel):
        super().__init__()

        self.state = model.state
        self._view = PayloadsEditorView()

        # payload bindings from model to view
        payloads = self.state.payloads
        payloads.events.added.connect(lambda d: self.payload_added(d["item"]))
        payloads.events.deleted.connect(self.payload_deleted)

        # payload bindings from view to model
        tab_widget = self._view.tabWidget
        tab_widget.addTabButton.clicked.connect(lambda _: self.add_payload())
        tab_widget.tabCloseRequested.connect(self.ask_delete_payload)
        tab_widget.tabMoved.connect(payloads.swap)

        def update_name(index: int) -> None:
            name = tab_widget.tabText(index)
            payload: Payload = payloads[index]
            payload.name = name

        tab_widget.editingFinished.connect(update_name)

        # initialize
        for payload in payloads:
            self._add_payload_bindings(payload)
            self.payload_added(payload)
        self._view.tabWidget.setCurrentIndex(0)

        self.validate()

    def payload_added(self, payload: Payload):
        formulations_editor = FormulationsEditor(payload.formulations)

        payload_editor = PayloadEditor(
            payload, formulations_editor_view=formulations_editor._view
        )
        self._view.tabWidget.addTab(payload_editor._view, payload.name)
        self._view.tabWidget.setCurrentWidget(payload_editor._view)

        self.validate()

    def payload_deleted(self, index: int) -> None:
        self._view.tabWidget.removeTab(index)

        self.validate()

    def add_payload(self):
        n_payloads = len(self.state.payloads)
        payload = Payload(name=f"New payload {n_payloads + 1}")
        self.state.payloads.append(payload)
        self._add_payload_bindings(payload)

    def _add_payload_bindings(self, payload: Payload):
        """
        All changes to the payload list trigger a call to the validate method.
        """
        payload.events.name.connect(lambda _: self.validate())
        payload.events.ang_dir.connect(lambda _: self.validate())
        payload.events.long_dir.connect(lambda _: self.validate())
        payload.events.long_orient.connect(lambda _: self.validate())

        def add_formulation_bindings(formulation: Formulation):
            formulation.events.name.connect(lambda _: self.validate())
            formulation.events.level.connect(lambda _: self.validate())
            formulation.angle.events.value.connect(lambda _: self.validate())

        payload.formulations.events.added.connect(
            lambda d: add_formulation_bindings(d["item"])
        )
        payload.formulations.events.changed.connect(lambda _: self.validate())
        for formulation in payload.formulations:
            add_formulation_bindings(formulation)

    def ask_delete_payload(self, index: int) -> None:
        name = self._view.tabWidget.tabText(index) or f"payload {index + 1}"
        response = showYesNoDialog(
            parent=self._view,
            title=f"Delete {name}?",
            text=f"Are you sure you want to delete {name}?",
        )
        if response != QMessageBox.Yes:
            return

        del self.state.payloads[index]
        self.log.debug(f"Payload {name} deleted")

    def validate(self) -> None:
        invalid_payload_indexes = self.state.invalid_payload_indexes()
        self._view.styleInvalidTabs(invalid_payload_indexes)
        self.is_valid = len(invalid_payload_indexes) == 0
