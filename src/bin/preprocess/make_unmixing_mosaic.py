import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import dask.array as da
import numpy as np
import numpy.typing as npt
from bmd_perf.profiling import timed_ctx
from dask import delayed as dask_delayed
from joblib import delayed as joblib_delayed, Parallel
from ome_types import from_xml
from skimage import img_as_float
from skimage.transform import downscale_local_mean
from tifffile import TiffReader, tifffile

from broadside.adjustments.alignment import (
    get_spectral_bands,
    get_scales_shifts,
    SpectralBand,
    shift_image,
    scale_image,
)
from broadside.adjustments.hot_pixels import get_remove_hot_pixels_func
from broadside.utils.arrays import square_concat
from broadside.utils.io import read_paths
from broadside.utils.parallel import dask_session


def read_tile(
    path: Path,
    *,
    remove_hot_pixels: Callable,
    flat_path: Path,
    dark_path: Path,
    scales: dict,
    shifts: dict,
    bands: list[SpectralBand],
    mid_chunk_size: int,
    downsample: int,
    max_value: int,
):
    image: npt.NDArray = tifffile.imread(path)

    # prepare mask
    mask = np.logical_or.reduce(image >= max_value, axis=0)
    assert mask.ndim == 2
    mask = mask.astype(float)

    image = img_as_float(image)
    image = remove_hot_pixels(image)

    # flatfield and darkfield take up a decent amount of space
    flatfield: npt.NDArray = tifffile.imread(flat_path)
    darkfield: npt.NDArray = tifffile.imread(dark_path)
    image -= darkfield
    image /= flatfield
    del flatfield
    del darkfield

    channels = []
    for channel, band in zip(image, bands):
        scale = scales[band.cube][band.wavelength]
        shift = shifts[band.cube][band.wavelength]
        channel = scale_image(channel, scale)
        channel = shift_image(channel, shift)
        channels.append(channel)
    image = np.stack(channels)

    # take middle chunk
    h, w = image.shape[-2:]
    h0 = max(0, h // 2 - mid_chunk_size // 2)
    h1 = min(h, h // 2 + mid_chunk_size // 2)
    w0 = max(0, w // 2 - mid_chunk_size // 2)
    w1 = min(w, w // 2 + mid_chunk_size // 2)

    image = image[:, h0:h1, w0:w1]
    mask = mask[h0:h1, w0:w1]

    scaled = downscale_local_mean(image, (1, downsample, downsample))
    mask = downscale_local_mean(mask, (downsample, downsample))
    # a little less than 1, to make sure that we get rid of blown out signal in the
    # downscaled image
    threshold = 0.8 / downsample
    scaled[:, mask > threshold] = 0
    # scaled = scaled[:, mask < threshold]
    scaled = scaled.clip(0, 1)
    return scaled


@dataclass(frozen=True)
class TileQC:
    path: Path
    ipr: float  # inter-percentile range


def get_ipr(path: Path, channel: int, mid_chunk_size: int) -> TileQC:
    with TiffReader(path) as tif:
        im = tif.pages[channel].asarray(maxworkers=1)
    assert im.ndim == 2
    h, w = im.shape

    h0 = max(0, h // 2 - mid_chunk_size // 2)
    h1 = min(h, h // 2 + mid_chunk_size // 2)
    w0 = max(0, w // 2 - mid_chunk_size // 2)
    w1 = min(w, w // 2 + mid_chunk_size // 2)

    im = im[h0:h1, w0:w1]
    p_lo, p_hi = np.percentile(im, (10, 90))
    return TileQC(path=path, ipr=(p_hi - p_lo).item())


def get_high_contrast_paths(
    paths: list[Path], *, n_tiles: int, channel: int, mid_chunk_size: int
):
    with timed_ctx("get tile contrasts"):
        tiles_qc: list[TileQC] = Parallel(n_jobs=-1, prefer="threads")(
            joblib_delayed(get_ipr)(
                path, channel=channel, mid_chunk_size=mid_chunk_size
            )
            for path in paths
        )
    tiles_by_ipr = sorted(tiles_qc, key=lambda tile: tile.ipr, reverse=True)
    return [tile.path for tile in tiles_by_ipr[:n_tiles]]


def make_unmixing_mosaic(
    *,
    tiles_path: Path,
    n_tiles: int,
    flat_path: Path,
    dark_path: Path,
    mid_chunk_size: int,
    downsample: int,
    dark_dir: Path,
    scales_shifts_dir: Path,
    ref_channel: int,
    dst: Path,
):
    """
    To generate the unmixing mosaic, we need a downsampled form of acquired images. The
    raw images are too noisy, and unmixing noisy images will result in noise.

    However, because saturated values are lost in the downsampling step in registration
    and stitching, we need to keep track of where they are and remove them from being
    included in the unmixing mosaic. This requires us to read the tiles themselves so
    that the proper adjustments can be made before assembling the mosaic.
    """

    # change this below, since we'll be getting the list explicitly in production
    paths = read_paths(tiles_path)
    paths = get_high_contrast_paths(
        paths, n_tiles=n_tiles, mid_chunk_size=mid_chunk_size, channel=ref_channel
    )

    # get exemplar tile metadata
    with TiffReader(paths[0]) as reader:
        shape = reader.series[0].shape
        ome = from_xml(reader.ome_metadata, parser="lxml")
        pixels = ome.images[0].pixels
        ts = ome.images[0].acquisition_date.timestamp()
        max_value = (2 ** int(pixels.significant_bits)) - 1

    # get calibration parameters
    remove_hot_pixels = get_remove_hot_pixels_func(ts, dark_dir=dark_dir)
    bands = get_spectral_bands(pixels)
    scales, shifts = get_scales_shifts(ts, scales_shifts_dir=scales_shifts_dir)

    new_shape = [shape[0], mid_chunk_size, mid_chunk_size]

    delayeds = [
        dask_delayed(read_tile)(
            path,
            remove_hot_pixels=remove_hot_pixels,
            flat_path=flat_path,
            dark_path=dark_path,
            scales=scales,
            shifts=shifts,
            bands=bands,
            mid_chunk_size=mid_chunk_size,
            downsample=downsample,
            max_value=max_value,
        )
        for path in paths
    ]
    delayeds = [da.from_delayed(d, shape=new_shape, dtype=float) for d in delayeds]
    stack = da.stack(delayeds)
    stack = stack.compute()
    mosaic = square_concat(list(stack))

    dst.parent.mkdir(exist_ok=True, parents=True)
    tifffile.imwrite(dst, mosaic, photometric="minisblack")


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tiles-path", type=str, required=True)
    parser.add_argument("--n-tiles", type=int, required=True)
    parser.add_argument("--flatfield-path", type=str, required=True)
    parser.add_argument("--darkfield-path", type=str, required=True)
    parser.add_argument("--mid-chunk-size", type=int, required=True)
    parser.add_argument("--downsample", type=int, required=True)
    parser.add_argument("--dark-dir", type=str, required=True)
    parser.add_argument("--scales-shifts-dir", type=str, required=True)
    parser.add_argument("--ref-channel", type=int, required=True)
    parser.add_argument("--dst", type=str, required=True)

    parser.add_argument("--n-cpus", type=int, default=None)
    parser.add_argument("--memory-limit", type=str, default=None)
    parser.add_argument("--dask-report-filename", type=str, default=None)

    args = parser.parse_args()

    with dask_session(
        memory_limit=args.memory_limit,
        n_cpus=args.n_cpus,
        dask_report_filename=args.dask_report_filename,
    ):
        make_unmixing_mosaic(
            tiles_path=Path(args.tiles_path),
            n_tiles=args.n_tiles,
            flat_path=Path(args.flatfield_path),
            dark_path=Path(args.darkfield_path),
            mid_chunk_size=args.mid_chunk_size,
            downsample=args.downsample,
            dark_dir=Path(args.dark_dir),
            scales_shifts_dir=Path(args.scales_shifts_dir),
            ref_channel=args.ref_channel,
            dst=Path(args.dst),
        )
