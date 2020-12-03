import cProfile
import pstats
from typing import Callable, Any


def cprofile(
    msg: str = None, *, sort_by: str = "cumtime", n_lines: int = 10
) -> Callable:
    """
    A simple decorator for seeing how long something takes.
    For in-depth profiling, use cProfile.

    Usage
    -----
    @profile()  # not sure how to use the decorator without parentheses in a nice way
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
            pr = cProfile.Profile()
            pr.enable()

            result = func(*args, **kwargs)

            pr.disable()
            print(msg)
            pstats.Stats().strip_dirs().sort_stats(sort_by).print_stats(n_lines)

            return result

        return inner

    return outer
