from typing import Optional, Type

from PySide2.QtCore import QObject, Signal, QThread


class Worker(QObject):
    """
    A way to run tasks separate from the main UI thread. Not the cleanest abstraction,
    but works for now at least.
    """

    started = Signal()
    finished = Signal()
    failed = Signal(Exception)
    data = Signal(dict)

    def stop(self) -> None:
        """
        Note that this won't actually have an effect if you don't check this condition
        in `task()`.
        """

        self._stopped = True

    def run(self) -> None:
        self.started.emit()

        self._stopped = False
        try:
            self.task()
        except Exception as e:
            self.failed.emit(e)
        else:
            self.finished.emit()

    def task(self, *args, **kwargs) -> None:
        """
        Subclasses of Worker must allow for checking the status of self._stopped so
        that the worker can be stopped in a responsive way.
        """
        raise NotImplementedError


class Runner:
    def __init__(self, workerCls: Type[Worker]):
        self.worker: Optional[Worker] = None
        self.thread: Optional[QThread] = None

        self.workerCls = workerCls

    def init(self) -> None:
        self.thread = QThread()

        self.worker = self.workerCls()
        self.worker.moveToThread(self.thread)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.fail)
        self.thread.started.connect(self.worker.run)
        self.thread.finished.connect(self.thread.deleteLater)

    def fail(self, e: Exception) -> None:
        raise e

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        if self.worker is not None:
            self.worker.stop()
        self.thread.quit()
        self.thread.wait()

    @property
    def data(self) -> Signal:
        return self.worker.data

    @property
    def started(self) -> Signal:
        return self.worker.started

    @property
    def finished(self) -> Signal:
        return self.worker.finished

    @property
    def failed(self) -> Signal:
        return self.worker.failed

    @property
    def is_running(self) -> bool:
        """
        Without this try-except block, Qt throws an error saying that the thread has
        already been deleted.
        """
        is_running = False
        try:
            if self.thread is not None:
                is_running = self.thread.isRunning()
        except RuntimeError:
            pass

        return is_running
