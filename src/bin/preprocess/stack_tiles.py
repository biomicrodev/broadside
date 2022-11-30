import argparse
from pathlib import Path
from typing import Callable

import dask.array as da
import numpy as np
import numpy.typing as npt
import tifffile
from dask import delayed
from ome_types import from_xml, OME
from ome_types.model import Image
from skimage import img_as_float
from skimage.util.dtype import _convert
from tifffile import TiffReader, TiffWriter

from broadside.adjustments.alignment import (
    SpectralBand,
    get_spectral_bands,
    get_scales_shifts,
    scale_image,
    shift_image,
)
from broadside.adjustments.hot_pixels import get_remove_hot_pixels_func
from broadside.utils.geoms import get_center_of_points
from broadside.utils.io import read_paths
from broadside.utils.parallel import dask_session

rotated_axes = [0, 2, 1]


def imrotate(stack: npt.NDArray) -> npt.NDArray:
    """
    The stage orients slides vertically; to fit the standard viewing orientation of
    slides, which is horizontally, we rotate images counter-clockwise, so that the label
    is on the left, and we rotate points counter-clockwise (i.e. X,Y -> Y,-X).
    """
    stack_rot = np.rot90(stack, axes=(1, 2))
    assert stack_rot.shape == tuple(stack.shape[i] for i in rotated_axes)
    return stack_rot


def read_tile_parallel(
    path: Path,
    *,
    remove_hot_pixels: Callable,
    flatfield_path: Path,
    darkfield_path: Path,
    scales: dict,
    shifts: dict,
    bands: list[SpectralBand],
    dtype: npt.DTypeLike,
):
    """
    The reason the workers have to read the flatfield and darkfield images instead of
    being passed the image is that when the function is passed to the worker, it makes
    copies of both and that is enough to completely use up the RAM. It's not ideal since
    we keep hammering the server...
    """

    image: npt.NDArray = tifffile.imread(path)
    image = img_as_float(image)
    image = remove_hot_pixels(image)

    # get illumination correction profiles
    flatfield: npt.NDArray = tifffile.imread(flatfield_path)
    darkfield: npt.NDArray = tifffile.imread(darkfield_path)
    image -= darkfield
    image /= flatfield
    del flatfield
    del darkfield

    assert len(image) == len(bands)

    chs = []
    for ch, band in zip(image, bands):
        scale = scales[band.cube][band.wavelength]
        shift = shifts[band.cube][band.wavelength]
        ch = scale_image(ch, scale)
        ch = shift_image(ch, shift)
        chs.append(ch)
    image = np.stack(chs)

    image.clip(0, 1, out=image)
    image = _convert(image, dtype)
    image = imrotate(image)
    return image


def read_ome(path: Path, ifd: int) -> Image:
    with TiffReader(path) as reader:
        ome = from_xml(reader.ome_metadata, parser="lxml")
        ome_image = ome.images[0]
        ome_image.pixels.tiff_data_blocks[0].ifd = ifd
    return ome_image


def update_stack_ome(first_ome: OME, tile_paths: list[Path]):
    n_channels = len(first_ome.images[0].pixels.channels)
    ome_images = [read_ome(p, ifd=i * n_channels) for i, p in enumerate(tile_paths)]

    # compute *center* position from all positions, not average *headdesk*
    pos_xx = []
    pos_yy = []
    for im in ome_images:
        plane = im.pixels.planes[0]
        pos_xx.append(plane.position_x)
        pos_yy.append(plane.position_y)
    center = get_center_of_points(pos_xx, pos_yy)

    # subtract center and rotate x and y
    for im in ome_images:
        im.pixels.size_x, im.pixels.size_y = im.pixels.size_y, im.pixels.size_x
        for plane in im.pixels.planes:
            pos_x = plane.position_x - center.x
            pos_y = plane.position_y - center.y

            plane.position_x, plane.position_y = pos_y, pos_x

    first_ome.images = ome_images
    return first_ome


def stack_tiles_parallel(
    tiles_path: Path,
    *,
    flatfield_path: Path,
    darkfield_path: Path,
    dark_dir: Path,
    scales_shifts_dir: Path,
    dst: Path,
):
    paths = read_paths(tiles_path)
    with TiffReader(paths[0]) as reader:
        dtype = reader.series[0].dtype
        shape = reader.series[0].shape

        ome = from_xml(reader.ome_metadata, parser="lxml")
        pixels = ome.images[0].pixels
        ts = ome.images[0].acquisition_date.timestamp()

    remove_hot_pixels = get_remove_hot_pixels_func(ts, dark_dir=dark_dir)
    bands = get_spectral_bands(pixels)
    scales, shifts = get_scales_shifts(ts, scales_shifts_dir=scales_shifts_dir)
    new_shape = [shape[i] for i in rotated_axes]

    delayeds = [
        delayed(read_tile_parallel)(
            path,
            remove_hot_pixels=remove_hot_pixels,
            flatfield_path=flatfield_path,
            darkfield_path=darkfield_path,
            scales=scales,
            shifts=shifts,
            bands=bands,
            dtype=dtype,
        )
        for path in paths
    ]
    delayeds = [da.from_delayed(d, shape=new_shape, dtype=dtype) for d in delayeds]
    stack = da.stack(delayeds)
    stack = stack.compute()

    updated_ome = update_stack_ome(ome, tile_paths=paths)
    dst.parent.mkdir(exist_ok=True, parents=True)
    tifffile.imwrite(
        dst,
        stack,
        photometric="minisblack",
        description=updated_ome.to_xml().encode(),
    )


def _adjust_channel(
    ch: npt.NDArray, scales: dict, shifts: dict, band: SpectralBand
) -> npt.NDArray:
    scale = scales[band.cube][band.wavelength]
    shift = shifts[band.cube][band.wavelength]
    ch = scale_image(ch, scale)
    ch = shift_image(ch, shift)
    return ch


def read_tile_serial(
    path: Path,
    *,
    remove_hot_pixels: Callable,
    flatfield: npt.NDArray,
    darkfield: npt.NDArray,
    scales: dict,
    shifts: dict,
    bands: list[SpectralBand],
    dtype: npt.DTypeLike,
):
    """
    The reason the workers have to read the flatfield and darkfield images instead of
    being passed the image is that when the function is passed to the worker, it makes
    copies of both and that is enough to completely use up the RAM. It's not ideal since
    we keep hammering the server...
    """

    image: npt.NDArray = tifffile.imread(path)
    image = img_as_float(image)
    image = remove_hot_pixels(image)

    image -= darkfield
    image /= flatfield

    assert len(image) == len(bands)

    chs = []
    for ch, band in zip(image, bands):
        scale = scales[band.cube][band.wavelength]
        shift = shifts[band.cube][band.wavelength]
        ch = scale_image(ch, scale)
        ch = shift_image(ch, shift)
        chs.append(ch)
    image = np.stack(chs)

    image.clip(0, 1, out=image)
    image = _convert(image, dtype)
    image = imrotate(image)
    return image


def stack_tiles(
    tiles_path: Path,
    *,
    flatfield_path: Path,
    darkfield_path: Path,
    dark_dir: Path,
    scales_shifts_dir: Path,
    dst: Path,
):
    paths = read_paths(tiles_path)
    with TiffReader(paths[0]) as reader:
        dtype = reader.series[0].dtype
        shape = reader.series[0].shape

        ome = from_xml(reader.ome_metadata, parser="lxml")
        pixels = ome.images[0].pixels
        ts = ome.images[0].acquisition_date.timestamp()

    remove_hot_pixels = get_remove_hot_pixels_func(ts, dark_dir=dark_dir)
    bands = get_spectral_bands(pixels)
    scales, shifts = get_scales_shifts(ts, scales_shifts_dir=scales_shifts_dir)
    new_shape = [shape[i] for i in rotated_axes]
    tile_shape = new_shape[1:]

    flatfield: npt.NDArray = tifffile.imread(flatfield_path)
    darkfield: npt.NDArray = tifffile.imread(darkfield_path)

    def _tiles():
        for path in paths:
            yield read_tile_serial(
                path,
                remove_hot_pixels=remove_hot_pixels,
                flatfield=flatfield,
                darkfield=darkfield,
                scales=scales,
                shifts=shifts,
                bands=bands,
                dtype=dtype,
            )

    updated_ome = update_stack_ome(ome, tile_paths=paths)
    dst.parent.mkdir(exist_ok=True, parents=True)
    with TiffWriter(dst, bigtiff=True) as tif:
        tif.write(
            data=_tiles(),
            tile=tile_shape,
            photometric="minisblack",
            description=updated_ome.to_xml().encode(),
            dtype=dtype,
            shape=[len(paths)] + new_shape,
        )


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tiles-path", type=str, required=True)
    parser.add_argument("--flatfield-path", type=str, required=True)
    parser.add_argument("--darkfield-path", type=str, required=True)
    parser.add_argument("--dark-dir", type=str, required=True)
    parser.add_argument("--scales-shifts-dir", type=str, required=True)
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
        stack_tiles_parallel(
            tiles_path=Path(args.tiles_path),
            flatfield_path=Path(args.flatfield_path),
            darkfield_path=Path(args.darkfield_path),
            dark_dir=Path(args.dark_dir),
            scales_shifts_dir=Path(args.scales_shifts_dir),
            dst=Path(args.dst),
        )
