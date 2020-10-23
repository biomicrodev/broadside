import datetime
import time
from typing import Callable, Any


def profile(msg: str = None, *, output: Callable = print) -> Callable:
    """
    A simple decorator for seeing how long something takes.
    For in-depth profiling, use cProfile.

    Usage
    -----
    @profile()
    def my_function():
        ...

    @profile("Time to run this function")
    def my_function():
        ...

    Parameters
    ----------
    msg : str
        A short description of the running task
    output : Callable
        Where to output profile results

    """

    if msg is None:
        msg = "Time to run"

    def outer(func: Callable) -> Callable:
        def inner(*args, **kwargs) -> Any:
            t0 = time.time()
            result = func(*args, **kwargs)
            t1 = time.time()

            elapsed_time = datetime.timedelta(seconds=t1 - t0)
            output(f"{msg}: {elapsed_time}")

            return result

        return inner

    return outer
