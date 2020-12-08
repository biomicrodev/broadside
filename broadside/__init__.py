import logging
import sys
from pathlib import Path

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication

from .gui.viewer import Viewer

logging.basicConfig(
    level=logging.DEBUG,
    stream=sys.stdout,
    format="%(asctime)-15s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger(__name__)


def run():
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)  # needed due to napari
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)

    app = QApplication()
    app.setApplicationName("Broadside")

    log.info("QApp started")

    Viewer(app=app, theme="light")

    sys.exit(app.exec_())
