import logging
import os
import sys
from pathlib import Path

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QApplication

logging.basicConfig(
    level=logging.DEBUG,
    stream=sys.stdout,
    format="%(asctime)-15s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger(__name__)

# for napari
os.environ["NAPARI_ASYNC"] = "1"
# os.environ["NAPARI_OCTREE"] = "1"

QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)

# import after setting environment variables
from .components.viewer import Viewer


def run():
    app = QApplication([])
    app.setApplicationName("Broadside")

    log.info("QApp started")

    viewer = Viewer(
        theme="light", path=Path("/home/sebastian/limbo/projects/test_project")
    )
    viewer.show()

    sys.exit(app.exec_())
