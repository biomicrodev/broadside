import numpy as np
import numpy.typing as npt


def find_nearest(x: float, vals: npt.NDArray) -> float:
    return vals[np.abs(vals - x).argmin()].item()


def find_k_minimum(arr: npt.NDArray, k: int) -> npt.NDArray:
    return arr[np.argpartition(arr, k)[:k]]
