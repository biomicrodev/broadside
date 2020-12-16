import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Set, NamedTuple, Optional

import dask.array as da
import numpy
import zarr
from tifffile import TiffFile, TiffPageSeries, TiffPage
from tifffile.tifffile import ZarrTiffStore
from zarr import Group

namespace = "{http://www.leica-microsystems.com/scn/2010/10/01}"

Layer = Dict[str, Any]


def str2int(s: str) -> int:
    return int(round(float(s)))


class Image(NamedTuple):
    name: str
    dtype: numpy.dtype
    channel_index: int
    n_channels: int
    axes: str
    file_format: str

    label: numpy.ndarray
    pyramids: List[Layer]

    background: Layer = None

    @classmethod
    def from_file(cls, path: Path):
        return normalize(path)


def parse_svs_metadata(s: str):
    software = s.split("\n")[0].strip()
    general = s.split("\n")[1].split("|")[0]

    properties = {
        p.split("=")[0].strip(): p.split("=")[1].strip()
        for p in s.split("\n")[1].split("|")[1:]
    }

    for key, value in properties.items():
        try:
            value = int(value)
        except ValueError:
            try:
                value = float(value)
            except ValueError:
                pass
            else:
                properties[key] = value
        else:
            properties[key] = value

    return {"software": software, "general": general, **properties}


def create_store(path: Path, name: str, level: int) -> ZarrTiffStore:
    with TiffFile(str(path)) as file:
        series = next(s for s in file.series if s.name == name)
        return series.aszarr(level)


def get_svs_pyramid(path: Path, series: TiffPageSeries) -> List[da.Array]:
    store: ZarrTiffStore = series.aszarr()
    group: Group = zarr.open(store, mode="r")
    levels: List[Dict[str, str]] = group.attrs["multiscales"][0]["datasets"]

    pyramid: List[da.Array] = []
    for level in levels:
        # create individual stores for each level to get around lock
        _store: ZarrTiffStore = create_store(path, series.name, int(level["path"]))
        array: da.Array = da.from_zarr(_store, chunks=("auto", "auto", "auto"))
        pyramid.append(array)

    # pyramid: List[da.Array] = [
    #     da.from_zarr(store, component=level["path"], chunks=("auto", "auto", 1))
    #     for level in levels
    # ]

    return pyramid


def get_scn_pyramids(
    path: Path, metadata: ET.Element, series: List[TiffPageSeries]
) -> List[Layer]:
    pyramids: List[Layer] = []
    names: List[str] = [s.name for s in series]
    for name in names:
        image_node: ET.Element = metadata.find(f'.//{namespace}image[@name="{name}"]')
        view_node: ET.Element = image_node.find(f".//{namespace}view")

        physical_size_x: float = str2int(view_node.get("sizeX")) / 1000
        physical_size_y: float = str2int(view_node.get("sizeY")) / 1000

        physical_offset_x: float = str2int(view_node.get("offsetX")) / 1000
        physical_offset_y: float = str2int(view_node.get("offsetY")) / 1000

        pixels_node: ET.Element = image_node.find(f".//{namespace}pixels")
        pixel_size_x: float = str2int(pixels_node.get("sizeX"))
        pixel_size_y: float = str2int(pixels_node.get("sizeY"))

        mpp_x: float = physical_size_x / pixel_size_x
        mpp_y: float = physical_size_y / pixel_size_y

        store: ZarrTiffStore = next(s for s in series if s.name == name).aszarr()
        group: Group = zarr.open(store, mode="r")
        levels: List[Dict[str, str]] = group.attrs["multiscales"][0]["datasets"]

        pyramid: List[da.Array] = []
        for level in levels:
            # create individual stores for each level to get around lock
            _store = create_store(path, name, int(level["path"]))
            array = da.from_zarr(_store, chunks=("auto", "auto", "auto"))
            pyramid.append(array)

        # pyramid: List[da.Array] = [
        #     da.from_zarr(store, component=level["path"], chunks=(1, "auto", "auto"))
        #     for level in levels
        # ]

        pyramids.append(
            {
                "layers": pyramid,
                "mpp": (mpp_y, mpp_x),
                "offset": (physical_offset_y, physical_offset_x),
            }
        )

    return pyramids


def normalize(path: Path) -> Optional[Image]:
    with TiffFile(str(path)) as file:
        if len(file.flags) > 1:
            print("more than one flag", file.flags)

        flags: Set[str] = file.flags
        series: List[TiffPageSeries] = file.series
        pages: List[TiffPage] = file.pages

        scn_metadata = file.scn_metadata

    # file format (svs or scn)
    file_format = list(flags)[0]

    if file_format == "svs":
        # get metadata
        metadata: Dict[str, Any] = parse_svs_metadata(pages[0].description)

        # get label
        label: numpy.ndarray = next(s for s in series if s.name == "Label").asarray()

        # get pyramids
        image: TiffPageSeries = next(s for s in series if s.name == "Baseline")
        pyramids = [
            {
                "layers": get_svs_pyramid(path, image),
                "mpp": (metadata["MPP"],) * 2,
                "offset": (0, 0),
            }
        ]

        axes: str = image.axes
        channel_index: int = list(axes).index("S")

        return Image(
            name=path.name,
            dtype=image.dtype,
            file_format=file_format,
            label=label,
            pyramids=pyramids,
            n_channels=image.shape[channel_index],
            channel_index=channel_index,
            axes=axes,
        )

    elif file_format == "scn":
        # get metadata
        metadata: ET.Element = ET.fromstring(scn_metadata)

        # get label
        label_ifd = int(
            metadata.find(f".//{namespace}supplementalImage[@type='label']").get("ifd")
        )
        label = next(p for p in pages if p.index == label_ifd).asarray()

        sources = {
            metadata.find(
                f'.//{namespace}image[@name="{s.name}"]'
                f"//{namespace}illuminationSource"
            ).text
            for s in series
        }

        if "fluorescence" in sources:
            series = [s for s in series if s.axes == "CYX"]
            axes = series[0].axes
            channel_index = list(axes).index("C")
            n_channels = series[0].shape[channel_index]
            pyramids = get_scn_pyramids(path, metadata, series)

            return Image(
                name=path.name,
                dtype=series[0].dtype,
                file_format=file_format,
                label=label,
                pyramids=pyramids,
                n_channels=n_channels,
                channel_index=channel_index,
                axes=axes,
            )

        else:
            axes = series[0].axes
            channel_index = list(axes).index("S")
            n_channels = series[0].shape[channel_index]
            pyramids = get_scn_pyramids(path, metadata, series)

            return Image(
                name=path.name,
                dtype=series[0].dtype,
                file_format=file_format,
                label=label,
                pyramids=pyramids[1:],
                n_channels=n_channels,
                channel_index=channel_index,
                axes=axes,
                background=pyramids[0],
            )
