from dataclasses import dataclass
from typing import Optional, Type, Callable, Any

from qtpy.QtCore import QObject, Signal, QThread, QTimer


@dataclass(frozen=True)
class Report:
    iter: int
    total: int


class Task(QObject):
    """
    A way to run tasks separate from the main UI thread. Not the cleanest abstraction,
    but works for now at least.
    """

    started = Signal()
    finished = Signal()
    failed = Signal(Exception)
    progress = Signal(Report)
    _progressThrottled = Signal(Report)
    result = Signal(object)

    def __init__(self, *args, **kwargs):
        super().__init__()

        self._args = args
        self._kwargs = kwargs

        self._lastReport: Optional[Report] = None

        self._timer = QTimer()
        self._timer.setInterval(30)

        def onTimeout():
            """
            progress: A...B...C...D...E...F...G...H...I...J
            lastrepo: AAAABBBBCCCCDDDDEEEEFFFFGGGGHHHHIIIIJ
            throttle: A.........C.........F.........H.........J
            """

            if self._lastReport is not None:
                self._progressThrottled.emit(self._lastReport)
            self._lastReport = None

        self._timer.timeout.connect(onTimeout)

        self.started.connect(self._timer.start)
        self.finished.connect(self._timer.stop)
        self.failed.connect(self._timer.stop)

        def setReport(report: Report) -> None:
            self._lastReport = report

        self.progress.connect(lambda r: setReport(r))

    def stop(self) -> None:
        """
        Note that this won't actually have an effect if you don't check this condition
        in `task()`.
        """

        self._stopped = True

    def execute(self) -> None:
        self.started.emit()

        self._stopped = False
        try:
            result = self.run(*self._args, **self._kwargs)
        except Exception as e:
            self.failed.emit(e)
        else:
            self.result.emit(result)
            self.finished.emit()

    def run(self, *args, **kwargs) -> Any:
        """
        Subclasses of Worker must allow for checking the status of self._stopped so
        that the worker can be stopped in a responsive way.
        """
        raise NotImplementedError


class Runner:
    """
    init -> register -> start
    init -> start -> register
    """

    def __init__(self, task_cls: Type[Task], *args, **kwargs):
        super().__init__()

        self.task: Optional[Task] = None
        self.thread: Optional[QThread] = None

        self._started = False

        self.task_cls = task_cls
        self._args = args
        self._kwargs = kwargs

    def init(self) -> None:
        if self._started:
            raise RuntimeError("Cannot init runner when task already started!")

        self.thread = QThread()

        self.task = self.task_cls(*self._args, **self._kwargs)
        self.task.moveToThread(self.thread)
        self.task.finished.connect(self.task.deleteLater)
        self.task.finished.connect(self.thread.quit)
        self.task.failed.connect(self.fail)
        self.thread.started.connect(self.task.execute)  # lambdas don't work here hm
        self.thread.finished.connect(self.thread.deleteLater)

    def register(
        self,
        *,
        started: Callable = None,
        finished: Callable = None,
        progress: Callable = None,
        failed: Callable = None,
        result: Callable = None
    ) -> None:
        if started is not None:
            self.task.started.connect(started)
        if finished is not None:
            self.task.finished.connect(finished)
        if progress is not None:
            self.task._progressThrottled.connect(progress)
        if failed is not None:
            self.task.failed.connect(failed)
        if result is not None:
            self.task.result.connect(result)

    def start(self) -> None:
        self._started = True
        self.thread.start()

    def stop(self) -> None:
        if self.task is not None:
            self.task.stop()

        if self.thread is not None:
            try:
                self.thread.quit()
                self.thread.wait()
            except RuntimeError:
                pass

        self._started = False

    def fail(self, e: Exception) -> None:
        raise e

    @property
    def is_running(self) -> bool:
        """
        Without this try-except block, Qt throws an error saying that the thread has
        already been deleted, even if `self.thread` is not None.
        """
        is_running = False
        try:
            if self.thread is not None:
                is_running = self.thread.isRunning()
        except RuntimeError:
            pass

        return is_running
