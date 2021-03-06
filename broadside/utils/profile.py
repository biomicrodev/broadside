import cProfile
import functools
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
    """

    def outer(func: Callable) -> Callable:
        @functools.wraps(func)
        def inner(*args, **kwargs) -> Any:
            pr = cProfile.Profile()
            pr.enable()

            try:
                result = func(*args, **kwargs)
            except Exception:
                raise
            else:
                return result
            finally:
                pr.disable()
                if msg:
                    print(msg)
                pstats.Stats(pr).strip_dirs().sort_stats(sort_by).print_stats(n_lines)

        return inner

    return outer
